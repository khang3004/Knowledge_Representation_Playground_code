
import os
import sys
import logging
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_db.connection import Neo4jConnection
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
from SPARQLWrapper import SPARQLWrapper, JSON

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ingest_chemistry")

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
DOMAIN = "chemistry"
BATCH_SIZE = 500
COLLECTION_NAME = "chemistry_facts"

# Massive SPARQL query for chemical reactions
# Q187939: chemical reaction
# P828: has reactant
# P1542: has product
SPARQL_QUERY_REACTIONS = """
SELECT DISTINCT ?reaction ?reactionLabel ?reactant ?reactantLabel ?reactantFormula ?product ?productLabel ?productFormula WHERE {
  ?reaction wdt:P31 wd:Q187939 .
  
  ?reaction p:P828 ?reactant_statement .
  ?reactant_statement ps:P828 ?reactant .
  ?reactant wdt:P274 ?reactantFormula .
  
  ?reaction p:P1542 ?product_statement .
  ?product_statement ps:P1542 ?product .
  ?product wdt:P274 ?productFormula .
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,vi" . }
}
LIMIT 2000
"""

class ChemistryIngest:
    def __init__(self):
        self.neo4j_conn = Neo4jConnection()
        self.qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.stats = {"facts": 0, "rules": 0}

    def fetch_wikidata_reactions(self) -> List[Dict[str, Any]]:
        logger.info("Fetching chemical reactions from Wikidata...")
        sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
        sparql.setQuery(SPARQL_QUERY_REACTIONS)
        sparql.setReturnFormat(JSON)
        sparql.addCustomHttpHeader("User-Agent", "Omni-IPS/2.0")
        
        try:
            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])
            logger.info(f"Retrieved {len(bindings)} reaction records.")
            return bindings
        except Exception as e:
            logger.error(f"SPARQL query failed: {e}")
            return []

    def process_data(self, bindings: List[Dict[str, Any]]):
        reactions = {}
        facts = {}
        
        for b in bindings:
            rid = b["reaction"]["value"].split("/")[-1]
            r_name = b["reactionLabel"]["value"]
            
            if rid not in reactions:
                reactions[rid] = {
                    "id": rid,
                    "name": r_name,
                    "inputs": set(),
                    "outputs": set(),
                    "domain": DOMAIN
                }
            
            # Process Reactants
            react_formula = b["reactantFormula"]["value"]
            react_label = b["reactantLabel"]["value"]
            reactions[rid]["inputs"].add(react_formula)
            facts[react_formula] = {"value": react_formula, "label": react_label, "domain": DOMAIN}
            
            # Process Products
            prod_formula = b["productFormula"]["value"]
            prod_label = b["productLabel"]["value"]
            reactions[rid]["outputs"].add(prod_formula)
            facts[prod_formula] = {"value": prod_formula, "label": prod_label, "domain": DOMAIN}

        # Convert sets to lists for JSON/Neo4j
        for r in reactions.values():
            r["inputs"] = list(r["inputs"])
            r["outputs"] = list(r["outputs"])
            
        return list(facts.values()), list(reactions.values())

    def load_to_neo4j(self, facts: List[Dict], rules: List[Dict]):
        logger.info(f"Loading {len(facts)} facts and {len(rules)} rules to Neo4j...")
        with self.neo4j_conn.get_session() as session:
            # Batch Load Facts with domain labels
            session.run("""
                UNWIND $batch AS row
                MERGE (f:Fact {value: row.value, domain: row.domain})
                ON CREATE SET f.id = 'fact_' + row.value, f.label = row.label
                SET f:Chemistry
            """, batch=facts)
            
            # Batch Load Rules with domain labels
            session.run("""
                UNWIND $batch AS row
                MERGE (r:Rule {id: row.id, domain: row.domain})
                ON CREATE SET r.name = row.name, r.description = 'Chemical reaction from Wikidata',
                              r.inputs = row.inputs, r.outputs = row.outputs
                SET r:Chemistry
            """, batch=rules)
            
            # Create Relationships
            session.run("""
                UNWIND $batch AS row
                MATCH (r:Rule {id: row.id, domain: row.domain})
                WITH r, row
                UNWIND row.inputs AS input_val
                MATCH (f_in:Fact {value: input_val, domain: row.domain})
                MERGE (f_in)-[:HAS_INPUT]->(r)
                WITH r, row
                UNWIND row.outputs AS output_val
                MATCH (f_out:Fact {value: output_val, domain: row.domain})
                MERGE (r)-[:HAS_OUTPUT]->(f_out)
            """, batch=rules)
            
        self.stats["facts"] += len(facts)
        self.stats["rules"] += len(rules)

    def load_to_qdrant(self, facts: List[Dict]):
        logger.info(f"Loading {len(facts)} facts to Qdrant...")
        points = []
        for i, f in enumerate(facts):
            vector = self.embed_model.encode(f"{f['label']} ({f['value']})").tolist()
            points.append(PointStruct(
                id=abs(hash(f['value'])) % (10**15),
                vector=vector,
                payload={"value": f['value'], "label": f['label'], "domain": DOMAIN}
            ))
            
            if len(points) >= BATCH_SIZE:
                self.qdrant_client.upsert(COLLECTION_NAME, points)
                points = []
        
        if points:
            self.qdrant_client.upsert(COLLECTION_NAME, points)

    def run(self):
        start_time = time.time()
        bindings = self.fetch_wikidata_reactions()
        if not bindings:
            return
            
        facts, rules = self.process_data(bindings)
        self.load_to_neo4j(facts, rules)
        self.load_to_qdrant(facts)
        
        duration = time.time() - start_time
        logger.info(f"ETL Complete in {duration:.2f}s. Stats: {self.stats}")

if __name__ == "__main__":
    ChemistryIngest().run()
