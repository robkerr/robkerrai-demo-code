"""CSV import functionality to populate Neo4j graph."""
import pandas as pd
import os
from typing import List, Set
from .database import db


def parse_multi_value_field(value: str) -> List[str]:
    """Parse comma-separated values from CSV field."""
    if pd.isna(value) or value == "":
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def import_movies_csv(csv_path: str = "movies.csv"):
    """Import movies from CSV file into Neo4j graph."""
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
    
    print(f"Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Found {len(df)} movies to import")
    
    if not db.driver:
        db.connect()
    
    db.create_indexes()
    
    # Track unique entities
    people: Set[str] = set()
    genres: Set[str] = set()
    companies: Set[str] = set()
    
    with db.driver.session() as session:
        # First, create all unique entities
        print("Creating entities...")
        
        for _, row in df.iterrows():
            # Collect people
            if pd.notna(row.get("director")):
                people.add(str(row["director"]).strip())
            if pd.notna(row.get("writer")):
                writers = parse_multi_value_field(row["writer"])
                people.update(writers)
            if pd.notna(row.get("actors")):
                actors = parse_multi_value_field(row["actors"])
                people.update(actors)
            
            # Collect genres
            if pd.notna(row.get("genre")):
                genre_list = parse_multi_value_field(row["genre"])
                genres.update(genre_list)
            
            # Collect production companies
            if pd.notna(row.get("production_company")):
                companies.add(str(row["production_company"]).strip())
        
        # Create Person nodes
        print(f"Creating {len(people)} Person nodes...")
        for person_name in people:
            session.run(
                "MERGE (p:Person {name: $name})",
                {"name": person_name}
            )
        
        # Create Genre nodes
        print(f"Creating {len(genres)} Genre nodes...")
        for genre_name in genres:
            session.run(
                "MERGE (g:Genre {name: $name})",
                {"name": genre_name}
            )
        
        # Create ProductionCompany nodes
        print(f"Creating {len(companies)} ProductionCompany nodes...")
        for company_name in companies:
            session.run(
                "MERGE (c:ProductionCompany {name: $name})",
                {"name": company_name}
            )
        
        # Create Movie nodes and relationships
        print("Creating Movie nodes and relationships...")
        for idx, row in df.iterrows():
            if (idx + 1) % 50 == 0:
                print(f"  Processed {idx + 1}/{len(df)} movies...")
            
            # Create Movie node
            movie_data = {
                "imdb_title_id": str(row["imdb_title_id"]) if pd.notna(row.get("imdb_title_id")) else None,
                "original_title": str(row["original_title"]) if pd.notna(row.get("original_title")) else "",
                "year": int(row["year"]) if pd.notna(row.get("year")) else None,
                "duration": int(row["duration"]) if pd.notna(row.get("duration")) else None,
                "description": str(row["description"]) if pd.notna(row.get("description")) else "",
                "avg_vote": float(row["avg_vote"]) if pd.notna(row.get("avg_vote")) else None,
                "votes": int(row["votes"]) if pd.notna(row.get("votes")) else None,
            }
            
            session.run("""
                MERGE (m:Movie {imdb_title_id: $imdb_title_id})
                SET m.original_title = $original_title,
                    m.year = $year,
                    m.duration = $duration,
                    m.description = $description,
                    m.avg_vote = $avg_vote,
                    m.votes = $votes
            """, movie_data)
            
            # Create relationships
            movie_id = movie_data["imdb_title_id"]
            
            # Director relationship
            if pd.notna(row.get("director")):
                director_name = str(row["director"]).strip()
                session.run("""
                    MATCH (m:Movie {imdb_title_id: $movie_id})
                    MATCH (p:Person {name: $director_name})
                    MERGE (p)-[:DIRECTED]->(m)
                """, {"movie_id": movie_id, "director_name": director_name})
            
            # Writer relationships
            if pd.notna(row.get("writer")):
                writers = parse_multi_value_field(row["writer"])
                for writer_name in writers:
                    session.run("""
                        MATCH (m:Movie {imdb_title_id: $movie_id})
                        MATCH (p:Person {name: $writer_name})
                        MERGE (p)-[:WROTE]->(m)
                    """, {"movie_id": movie_id, "writer_name": writer_name})
            
            # Actor relationships
            if pd.notna(row.get("actors")):
                actors = parse_multi_value_field(row["actors"])
                for actor_name in actors:
                    session.run("""
                        MATCH (m:Movie {imdb_title_id: $movie_id})
                        MATCH (p:Person {name: $actor_name})
                        MERGE (p)-[:ACTED_IN]->(m)
                    """, {"movie_id": movie_id, "actor_name": actor_name})
            
            # Genre relationships
            if pd.notna(row.get("genre")):
                genre_list = parse_multi_value_field(row["genre"])
                for genre_name in genre_list:
                    session.run("""
                        MATCH (m:Movie {imdb_title_id: $movie_id})
                        MATCH (g:Genre {name: $genre_name})
                        MERGE (m)-[:HAS_GENRE]->(g)
                    """, {"movie_id": movie_id, "genre_name": genre_name})
            
            # Production company relationship
            if pd.notna(row.get("production_company")):
                company_name = str(row["production_company"]).strip()
                session.run("""
                    MATCH (m:Movie {imdb_title_id: $movie_id})
                    MATCH (c:ProductionCompany {name: $company_name})
                    MERGE (m)-[:PRODUCED_BY]->(c)
                """, {"movie_id": movie_id, "company_name": company_name})
        
        print(f"Successfully imported {len(df)} movies into Neo4j!")


if __name__ == "__main__":
    db.connect()
    import_movies_csv()
    db.close()

