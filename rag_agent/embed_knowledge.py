"""
Vector Ingestion & Embedding Pipeline for Omni-IPS.

Fetches all Fact and Rule nodes from the Neo4j Knowledge Graph,
generates local vector embeddings using ChromaDB's default embedding function,
and populates the Chroma Vector Database.
"""

import os
import sys
import logging
import argparse
from typing import List, Dict, Any

# Add project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.utils import embedding_functions
from graph_db.connection import Neo4jConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("embed_knowledge")


def get_neo4j_facts_and_rules() -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Queries all Facts and Rules from Neo4j."""
    conn = Neo4jConnection()
    if not conn.verify_connectivity():
        logger.error("Failed to connect to Neo4j. Ingestion aborted.")
        sys.exit(1)

    facts = []
    rules = []

    with conn:
        with conn.get_session() as session:
            logger.info("Fetching Fact nodes from Neo4j...")
            fact_result = session.run(
                "MATCH (f:Fact) "
                "RETURN f.id AS id, f.value AS value, f.domain AS domain, f.label AS label, f.formula AS formula"
            )
            for record in fact_result:
                facts.append({
                    "id": record["id"],
                    "value": record["value"],
                    "domain": record["domain"],
                    "label": record["label"] or record["value"],
                    "formula": record["formula"] or ""
                })
            logger.info("Successfully fetched %d Facts.", len(facts))

            logger.info("Fetching Rule nodes from Neo4j...")
            rule_result = session.run(
                "MATCH (r:Rule) "
                "RETURN r.id AS id, r.name AS name, r.domain AS domain, r.description AS description, r.source AS source"
            )
            for record in rule_result:
                rules.append({
                    "id": record["id"],
                    "name": record["name"],
                    "domain": record["domain"],
                    "description": record["description"] or "",
                    "source": record["source"] or "Unknown"
                })
            logger.info("Successfully fetched %d Rules.", len(rules))

    return facts, rules


def ingest_to_chroma(facts: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> None:
    """Ingests generated documents and metadata into ChromaDB collections."""
    chroma_host = os.getenv("CHROMADB_HOST", "localhost")
    chroma_port = int(os.getenv("CHROMADB_PORT", 8000))

    logger.info("Connecting to ChromaDB at %s:%d...", chroma_host, chroma_port)
    try:
        chroma_client = chromadb.HttpClient(host=chroma_host, port=str(chroma_port))
    except Exception as e:
        logger.error("Failed to connect to ChromaDB: %s", e)
        sys.exit(1)

    # Initialize Chroma's local embedding function (SentenceTransformer/ONNX)
    default_ef = embedding_functions.DefaultEmbeddingFunction()

    # Recreate collection for Facts
    logger.info("Recreating Chroma collection 'omni_ips_facts'...")
    try:
        chroma_client.delete_collection("omni_ips_facts")
    except Exception:
        pass
    facts_collection = chroma_client.create_collection(
        name="omni_ips_facts", 
        embedding_function=default_ef
    )

    # Recreate collection for Rules
    logger.info("Recreating Chroma collection 'omni_ips_rules'...")
    try:
        chroma_client.delete_collection("omni_ips_rules")
    except Exception:
        pass
    rules_collection = chroma_client.create_collection(
        name="omni_ips_rules", 
        embedding_function=default_ef
    )

    # Ingest Facts
    if facts:
        logger.info("Upserting Facts into ChromaDB...")
        ids = []
        documents = []
        metadatas = []

        for fact in facts:
            # Generate a semantic document for Vector search matching
            doc = f"Fact in domain '{fact['domain']}': {fact['label']}"
            if fact['formula']:
                doc += f" ({fact['formula']})"
            doc += f" with representation value of {fact['value']}."

            ids.append(f"fact_{fact['domain']}_{fact['value']}")
            documents.append(doc)
            metadatas.append({
                "neo4j_id": fact["id"],
                "value": fact["value"],
                "domain": fact["domain"],
                "label": fact["label"],
                "type": "fact"
            })

        # ChromaDB upsert (batch operations supported)
        facts_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info("Successfully ingested %d Fact vectors.", len(facts))

    # Ingest Rules
    if rules:
        logger.info("Upserting Rules into ChromaDB...")
        ids = []
        documents = []
        metadatas = []

        for rule in rules:
            # Generate semantic rule document
            doc = f"Rule in domain '{rule['domain']}': name is '{rule['name']}'"
            if rule['description']:
                doc += f", described as: {rule['description']}"
            doc += f". Verified from source: {rule['source']}"

            ids.append(f"rule_{rule['domain']}_{rule['id']}")
            documents.append(doc)
            metadatas.append({
                "neo4j_id": rule["id"],
                "name": rule["name"],
                "domain": rule["domain"],
                "type": "rule"
            })

        rules_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info("Successfully ingested %d Rule vectors.", len(rules))

    logger.info("ChromaDB synchronization complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Synchronize Neo4j Knowledge base Facts and Rules to Chroma Vector database."
    )
    parser.parse_args()

    facts, rules = get_neo4j_facts_and_rules()
    
    if not facts and not rules:
        logger.warning("No Facts or Rules found in Neo4j to embed. Populating local collections empty.")
        
    ingest_to_chroma(facts, rules)


if __name__ == "__main__":
    main()
