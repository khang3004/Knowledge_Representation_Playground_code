"""
Vector Ingestion & Embedding Pipeline for Omni-IPS.

Fetches all Fact and Rule nodes from the Neo4j Knowledge Graph,
generates local vector embeddings using SentenceTransformers (all-MiniLM-L6-v2),
and populates the Qdrant Vector Database.
"""

import os
import sys
import time
import logging
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load local environment configurations from .env
load_dotenv()

# Add project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from graph_db.connection import Neo4jConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("embed_knowledge")

# Embedding model — all-MiniLM-L6-v2 (384-dim, fast, high-quality semantic similarity)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


def get_qdrant_client(max_retries: int = 5, backoff_base: float = 2.0) -> QdrantClient:
    """Creates a Qdrant client with retry logic for startup robustness."""
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))

    for attempt in range(1, max_retries + 1):
        try:
            client = QdrantClient(host=qdrant_host, port=qdrant_port)
            # Verify connectivity
            client.get_collections()
            logger.info("Connected to Qdrant at %s:%d (attempt %d)", qdrant_host, qdrant_port, attempt)
            return client
        except Exception as e:
            if attempt == max_retries:
                logger.error("Failed to connect to Qdrant after %d attempts: %s", max_retries, e)
                sys.exit(1)
            wait_time = backoff_base ** attempt
            logger.warning("Qdrant connection attempt %d/%d failed: %s. Retrying in %.1fs...",
                           attempt, max_retries, e, wait_time)
            time.sleep(wait_time)


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


def ingest_to_qdrant(facts: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> None:
    """Ingests generated documents and metadata into Qdrant collections."""
    client = get_qdrant_client()

    logger.info("Loading embedding model '%s'...", EMBEDDING_MODEL_NAME)
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # Recreate collection for Facts
    logger.info("Recreating Qdrant collection 'omni_ips_facts'...")
    try:
        client.delete_collection("omni_ips_facts")
    except Exception:
        pass
    client.create_collection(
        collection_name="omni_ips_facts",
        vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE)
    )

    # Recreate collection for Rules
    logger.info("Recreating Qdrant collection 'omni_ips_rules'...")
    try:
        client.delete_collection("omni_ips_rules")
    except Exception:
        pass
    client.create_collection(
        collection_name="omni_ips_rules",
        vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE)
    )

    # Ingest Facts
    if facts:
        logger.info("Embedding and uploading Facts into Qdrant...")
        documents = []
        points = []

        for idx, fact in enumerate(facts):
            # Generate a semantic document for vector search matching
            doc = f"Fact in domain '{fact['domain']}': {fact['label']}"
            if fact['formula']:
                doc += f" ({fact['formula']})"
            doc += f" with representation value of {fact['value']}."
            documents.append(doc)

        # Batch encode all fact documents
        embeddings = model.encode(documents, show_progress_bar=True)

        for idx, (fact, embedding) in enumerate(zip(facts, embeddings)):
            points.append(PointStruct(
                id=idx,
                vector=embedding.tolist(),
                payload={
                    "neo4j_id": fact["id"],
                    "value": fact["value"],
                    "domain": fact["domain"],
                    "label": fact["label"],
                    "type": "fact"
                }
            ))

        # Bulk upload
        client.upsert(collection_name="omni_ips_facts", points=points)
        logger.info("Successfully ingested %d Fact vectors.", len(facts))

    # Ingest Rules
    if rules:
        logger.info("Embedding and uploading Rules into Qdrant...")
        documents = []
        points = []

        for idx, rule in enumerate(rules):
            # Generate semantic rule document
            doc = f"Rule in domain '{rule['domain']}': name is '{rule['name']}'"
            if rule['description']:
                doc += f", described as: {rule['description']}"
            doc += f". Verified from source: {rule['source']}"
            documents.append(doc)

        # Batch encode all rule documents
        embeddings = model.encode(documents, show_progress_bar=True)

        for idx, (rule, embedding) in enumerate(zip(rules, embeddings)):
            points.append(PointStruct(
                id=idx,
                vector=embedding.tolist(),
                payload={
                    "neo4j_id": rule["id"],
                    "name": rule["name"],
                    "domain": rule["domain"],
                    "type": "rule"
                }
            ))

        client.upsert(collection_name="omni_ips_rules", points=points)
        logger.info("Successfully ingested %d Rule vectors.", len(rules))

    logger.info("Qdrant synchronization complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Synchronize Neo4j Knowledge base Facts and Rules to Qdrant Vector database."
    )
    parser.parse_args()

    facts, rules = get_neo4j_facts_and_rules()
    
    if not facts and not rules:
        logger.warning("No Facts or Rules found in Neo4j to embed. Populating local collections empty.")
        
    ingest_to_qdrant(facts, rules)


if __name__ == "__main__":
    main()
