"""Neo4j database connection and graph operations."""
import os
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase, Driver


class Neo4jDatabase:
    """Manages Neo4j database connection and operations."""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "neo4j://neo4j:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "cinegraph123")
        self.driver: Optional[Driver] = None
    
    def connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verify connectivity
            self.driver.verify_connectivity()
            print(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")
    
    def has_data(self) -> bool:
        """Check if the graph has any Movie nodes."""
        if not self.driver:
            self.connect()
        
        with self.driver.session() as session:
            result = session.run("MATCH (m:Movie) RETURN count(m) as count")
            record = result.single()
            count = record["count"] if record else 0
            return count > 0
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if not self.driver:
            self.connect()
        
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def create_indexes(self):
        """Create indexes for better query performance."""
        indexes = [
            "CREATE INDEX movie_title_idx IF NOT EXISTS FOR (m:Movie) ON (m.original_title)",
            "CREATE INDEX movie_year_idx IF NOT EXISTS FOR (m:Movie) ON (m.year)",
            "CREATE INDEX person_name_idx IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX genre_name_idx IF NOT EXISTS FOR (g:Genre) ON (g.name)",
        ]
        
        if not self.driver:
            self.connect()
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    print(f"Created index: {index_query[:50]}...")
                except Exception as e:
                    # Index might already exist, which is fine
                    print(f"Index creation note: {e}")


# Global database instance
db = Neo4jDatabase()

