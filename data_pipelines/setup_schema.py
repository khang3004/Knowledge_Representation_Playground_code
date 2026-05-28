
import os
import logging
import sys
from dotenv import load_dotenv

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_db.connection import Neo4jConnection
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_schema")

def setup_neo4j_constraints():
    """Create constraints for strict multi-domain partitioning."""
    logger.info("Setting up Neo4j constraints...")
    conn = Neo4jConnection()
    with conn.get_session() as session:
        # Fact constraint: unique (id, domain)
        # Note: Neo4j 4.4+ supports uniqueness constraints on multiple properties
        try:
            session.run("CREATE CONSTRAINT fact_id_domain_unique IF NOT EXISTS FOR (f:Fact) REQUIRE (f.id, f.domain) IS UNIQUE")
            session.run("CREATE CONSTRAINT rule_id_domain_unique IF NOT EXISTS FOR (r:Rule) REQUIRE (r.id, r.domain) IS UNIQUE")
            
            # Additional labels constraints
            session.run("CREATE INDEX fact_domain_idx IF NOT EXISTS FOR (f:Fact) ON (f.domain)")
            session.run("CREATE INDEX rule_domain_idx IF NOT EXISTS FOR (r:Rule) ON (r.domain)")
            
            logger.info("Neo4j constraints and indices created successfully.")
        except Exception as e:
            logger.error(f"Failed to create Neo4j constraints: {e}")
    conn.close()

def setup_qdrant_collections():
    """Create isolated Qdrant collections per domain."""
    logger.info("Setting up Qdrant collections...")
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    
    domains = ["chemistry", "geometry", "algebra"]
    vector_size = 384  # MiniLM-L6-v2 size
    
    for domain in domains:
        collection_name = f"{domain}_facts"
        try:
            if not client.collection_exists(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection {collection_name}: {e}")

if __name__ == "__main__":
    setup_neo4j_constraints()
    setup_qdrant_collections()
