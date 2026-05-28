
import os
import sys
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import sympy
from sympy.abc import x, y, z

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_db.connection import Neo4jConnection
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_algebra")

DOMAIN = "algebra"
COLLECTION_NAME = "algebra_facts"

ALGEBRA_RULES = [
    {
        "id": "alg_commutative_add",
        "name": "Commutative Property of Addition",
        "inputs": ["x+y"],
        "outputs": ["y+x"],
        "description": "a + b = b + a"
    },
    {
        "id": "alg_distributive",
        "name": "Distributive Property",
        "inputs": ["x*(y+z)"],
        "outputs": ["x*y + x*z"],
        "description": "a(b + c) = ab + ac"
    },
    {
        "id": "alg_sub_both_sides",
        "name": "Subtraction Property of Equality",
        "inputs": ["Equation(LHS, RHS)", "Subtract(Val)"],
        "outputs": ["Equation(LHS-Val, RHS-Val)"],
        "description": "If a = b, then a - c = b - c"
    },
    {
        "id": "alg_add_both_sides",
        "name": "Addition Property of Equality",
        "inputs": ["Equation(LHS, RHS)", "Add(Val)"],
        "outputs": ["Equation(LHS+Val, RHS+Val)"],
        "description": "If a = b, then a + c = b + c"
    },
    {
        "id": "alg_identity_mul",
        "name": "Multiplicative Identity",
        "inputs": ["x*1"],
        "outputs": ["x"],
        "description": "a * 1 = a"
    },
    {
        "id": "alg_sub_two",
        "name": "Subtraction Property of 2",
        "inputs": ["x+2=5", "Subtract(2,both_sides)"],
        "outputs": ["x=3"],
        "description": "Subtract 2 from both sides of the equation x+2=5 to yield x=3."
    }
]

class AlgebraIngest:
    def __init__(self):
        self.neo4j_conn = Neo4jConnection()
        self.qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    def load_to_neo4j(self):
        logger.info("Loading Algebra rules to Neo4j...")
        with self.neo4j_conn.get_session() as session:
            # Load Rules
            session.run("""
                UNWIND $batch AS row
                MERGE (r:Rule {id: row.id, domain: $domain})
                ON CREATE SET r.name = row.name, r.description = row.description,
                              r.inputs = row.inputs, r.outputs = row.outputs
                SET r:Algebra
            """, batch=ALGEBRA_RULES, domain=DOMAIN)
            
            # Extract and load facts (entities) from inputs/outputs
            all_facts = set()
            for r in ALGEBRA_RULES:
                all_facts.update(r["inputs"])
                all_facts.update(r["outputs"])
            
            fact_data = [{"value": f, "label": f, "domain": DOMAIN} for f in all_facts]
            
            session.run("""
                UNWIND $batch AS row
                MERGE (f:Fact {value: row.value, domain: row.domain})
                ON CREATE SET f.id = 'alg_fact_' + row.value, f.label = row.label
                SET f:Algebra
            """, batch=fact_data)
            
            # Create Relationships
            session.run("""
                UNWIND $batch AS row
                MATCH (r:Rule {id: row.id, domain: $domain})
                WITH r, row
                UNWIND row.inputs AS input_val
                MATCH (f_in:Fact {value: input_val, domain: $domain})
                MERGE (f_in)-[:HAS_INPUT]->(r)
                WITH r, row
                UNWIND row.outputs AS output_val
                MATCH (f_out:Fact {value: output_val, domain: $domain})
                MERGE (r)-[:HAS_OUTPUT]->(f_out)
            """, batch=ALGEBRA_RULES, domain=DOMAIN)

    def load_to_qdrant(self):
        logger.info("Loading Algebra facts to Qdrant...")
        all_facts = set()
        for r in ALGEBRA_RULES:
            all_facts.update(r["inputs"])
            all_facts.update(r["outputs"])
            
        points = []
        for f_val in all_facts:
            vector = self.embed_model.encode(f_val).tolist()
            points.append(PointStruct(
                id=abs(hash(f_val)) % (10**15),
                vector=vector,
                payload={"value": f_val, "label": f_val, "domain": DOMAIN}
            ))
            
        if points:
            self.qdrant_client.upsert(COLLECTION_NAME, points)

    def run(self):
        self.load_to_neo4j()
        self.load_to_qdrant()
        logger.info("Algebra ingestion complete.")

if __name__ == "__main__":
    AlgebraIngest().run()
