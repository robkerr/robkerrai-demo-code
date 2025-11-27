"""GraphRAG query implementation using Neo4j Cypher."""
import time
from typing import List, Dict, Any, Optional, Tuple
from .database import db
from .llm_client import llm_client

def query_movies_by_actor_and_genre(actor_name: str, genre: str) -> List[Dict[str, Any]]:
    """Find movies by actor and genre."""
    query = """
        MATCH (p:Person {name: $actor_name})-[:ACTED_IN]->(m:Movie)-[:HAS_GENRE]->(g:Genre {name: $genre})
        RETURN m.original_title as title,
               m.year as year,
               m.description as description,
               m.avg_vote as rating,
               m.imdb_title_id as imdb_id
        ORDER BY m.avg_vote DESC
    """

    print("--------------------------------")
    print(f"Actor: {actor_name}")
    print(f"Genre: {genre}")
    print(f"Executing query: {query}")
    print("--------------------------------")

    return db.execute_query(query, {"actor_name": actor_name, "genre": genre})

def query_movies_by_director_and_actor(director_name: str, actor_name: str) -> List[Dict[str, Any]]:
    """Find movies by director and actor."""
    query = """
        MATCH (director:Person {name: $director_name})-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(actor:Person {name: $actor_name})
        RETURN 
            director.name AS director, 
            actor.name AS actor, 
            m.original_title AS original_title, m.genres AS genres,
            m.year AS year
        ORDER BY year DESC
    """

    print("--------------------------------")
    print(f"Director: {director_name}")
    print(f"Actor: {actor_name}")
    print(f"Executing query: {query}")
    print("--------------------------------")

    return db.execute_query(query, {"director_name": director_name, "actor_name": actor_name})

def query_movies_by_keywords(keyword_list: List[str]) -> List[Dict[str, Any]]:
    """Find movies by description keywords using full-text search."""
    # Build regex pattern for case-insensitive matching
    # Escape special regex characters in keywords and join with |
    import re
    escaped_keywords = [re.escape(keyword) for keyword in keyword_list]
    pattern = '(?i).*(' + '|'.join(escaped_keywords) + ').*'
    
    query = """
        MATCH (m:Movie)
        WHERE m.description IS NOT NULL
          AND m.description =~ $pattern
        RETURN m.original_title as title,
               m.year as year,
               m.description as description,
               m.avg_vote as rating,
               m.imdb_title_id as imdb_id
        ORDER BY m.avg_vote DESC
    """

    print("--------------------------------")
    print(f"Keywords: {keyword_list}")
    print(f"Executing query: {query}")
    print(f"Pattern: {pattern}")
    print("--------------------------------")

    graph_response = db.execute_query(query, {"pattern": pattern})
    return graph_response


def execute_graphrag_query(question: str) -> Tuple[List[Dict[str, Any]], Dict[str, int], float, float]:
    """
    Execute a GraphRAG query based on the user's question.
    Returns tuple of (movie_results, analysis_token_usage, analysis_time, query_time).
    """
    # Analyze the question to determine what type of question it is and extract the relevant key terms
    analysis, analysis_token_usage, analysis_time = llm_client.analyze_query(question)
    query_type = analysis["type"]

    print("--------------------------------")
    print(f"Query type: {query_type}")
    print(f"Analysis: {analysis}")
    print(f"Analysis token usage: {analysis_token_usage}")
    print(f"Analysis time: {analysis_time}")
    print("--------------------------------")
    
    # Execute the actual GraphRAG query (track timing separately)
    query_start_time = time.time()
    
    if query_type == "actor_genre":
        graphrag_results = query_movies_by_actor_and_genre(analysis["actor"], analysis["genre"])
    elif query_type == "director_actor":
        graphrag_results = query_movies_by_director_and_actor(analysis["director"], analysis["actor"])
    elif query_type == "keywords":
         graphrag_results = query_movies_by_keywords(analysis["keywords"])

    query_time = time.time() - query_start_time
    
    return graphrag_results, analysis_token_usage, analysis_time, query_time

