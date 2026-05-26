"""
Neo4j Connection Manager for Omni-IPS.

Provides a thread-safe driver singleton and session context manager
for all ETL pipelines and query operations.
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Generator

from neo4j import GraphDatabase, Driver, Session

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """
    Manages a single Neo4j driver instance with environment-based configuration.

    Usage:
        conn = Neo4jConnection()
        with conn.get_session() as session:
            session.run("MATCH (n) RETURN count(n)")
        conn.close()
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self._uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self._user = user or os.getenv("NEO4J_USER", "neo4j")
        self._password = password or os.getenv("NEO4J_PASSWORD", "omni_ips_password")
        self._driver: Optional[Driver] = None

    def _get_driver(self) -> Driver:
        """Lazily initializes and returns the Neo4j driver singleton."""
        if self._driver is None:
            logger.info("Initializing Neo4j driver for %s", self._uri)
            self._driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
        return self._driver

    @contextmanager
    def get_session(self, database: str = "neo4j") -> Generator[Session, None, None]:
        """
        Context manager yielding a Neo4j session.
        Ensures proper cleanup on exit.
        """
        driver = self._get_driver()
        session = driver.session(database=database)
        try:
            yield session
        finally:
            session.close()

    def verify_connectivity(self) -> bool:
        """
        Performs a lightweight connectivity health check against the Neo4j instance.
        Returns True if reachable, False otherwise.
        """
        try:
            driver = self._get_driver()
            driver.verify_connectivity()
            logger.info("Neo4j connectivity verified successfully at %s", self._uri)
            return True
        except Exception as e:
            logger.error("Neo4j connectivity check failed: %s", e)
            return False

    def close(self) -> None:
        """Closes the driver and releases all resources."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j driver closed.")

    def __enter__(self) -> "Neo4jConnection":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
