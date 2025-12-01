#!/usr/bin/env python3
"""
Import movie data from CSV into Azure Cosmos DB (Gremlin API)

This script:
1. Parses a CSV file with movie data
2. Creates graph vertices for Movies, People, Genres, Production Companies
3. Creates edges for relationships (ACTED_IN, DIRECTED, WROTE, HAS_GENRE, PRODUCED_BY)
"""

import csv
import os
import sys
from typing import Dict, List, Set
from gremlin_python.driver import client, serializer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cosmos DB connection settings
COSMOS_ENDPOINT = os.getenv('COSMOS_ENDPOINT')
COSMOS_KEY = os.getenv('COSMOS_KEY')
COSMOS_DATABASE = os.getenv('COSMOS_DATABASE', 'moviedb')
COSMOS_COLLECTION = os.getenv('COSMOS_COLLECTION', 'movies')


class MovieGraphImporter:
    """Imports movie data into Cosmos DB Gremlin graph"""

    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.gremlin_client = None
        self.stats = {
            'movies': 0,
            'people': 0,
            'genres': 0,
            'companies': 0,
            'acted_in': 0,
            'directed': 0,
            'wrote': 0,
            'has_genre': 0,
            'produced_by': 0
        }
        # Track unique entities to avoid duplicates
        self.people_cache: Set[str] = set()
        self.genre_cache: Set[str] = set()
        self.company_cache: Set[str] = set()

    def connect(self):
        """Establish connection to Cosmos DB Gremlin API"""
        if not COSMOS_ENDPOINT or not COSMOS_KEY:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY must be set in environment variables")

        print(f"Connecting to Cosmos DB at {COSMOS_ENDPOINT}...")

        self.gremlin_client = client.Client(
            url=COSMOS_ENDPOINT,
            traversal_source='g',
            username=f"/dbs/{COSMOS_DATABASE}/colls/{COSMOS_COLLECTION}",
            password=COSMOS_KEY,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )

        print("Connected successfully!")

    def close(self):
        """Close the connection"""
        if self.gremlin_client:
            self.gremlin_client.close()

    def execute_query(self, query: str) -> List:
        """Execute a Gremlin query and return results"""
        try:
            callback = self.gremlin_client.submitAsync(query)
            result = callback.result()
            return result.all().result()
        except Exception as e:
            print(f"Error executing query: {query}")
            print(f"Error: {e}")
            return []

    def clear_graph(self):
        """Clear all vertices and edges from the graph (use with caution!)"""
        print("Clearing existing graph data...")
        self.execute_query("g.V().drop()")
        print("Graph cleared!")

    def add_person_vertex(self, name: str) -> str:
        """Add a Person vertex if it doesn't exist"""
        name = name.strip()
        if name in self.people_cache:
            return name

        # Create vertex with name as both id and property
        person_id = name.replace("'", "\\'")
        query = (
            "g.addV('Person')"
            f".property('id', '{person_id}')"
            f".property('name', '{person_id}')"
            ".property('pk', 'Person')"           # <-- partition key
        )
        self.execute_query(query)

        self.people_cache.add(name)
        self.stats['people'] += 1
        return name

    def add_genre_vertex(self, genre: str) -> str:
        """Add a Genre vertex if it doesn't exist"""
        genre = genre.strip()
        if genre in self.genre_cache:
            return genre

        genre_id = genre.replace("'", "\\'")
        query = (
            "g.addV('Genre')"
            f".property('id', '{genre_id}')"
            f".property('name', '{genre_id}')"
            ".property('pk', 'Genre')"            # <-- partition key
        )
        self.execute_query(query)

        self.genre_cache.add(genre)
        self.stats['genres'] += 1
        return genre

    def add_company_vertex(self, company: str) -> str:
        """Add a ProductionCompany vertex if it doesn't exist"""
        company = company.strip()
        if company in self.company_cache:
            return company

        company_id = company.replace("'", "\\'")
        query = (
            "g.addV('ProductionCompany')"
            f".property('id', '{company_id}')"
            f".property('name', '{company_id}')"
            ".property('pk', 'ProductionCompany')"    # <-- partition key
        )
        self.execute_query(query)

        self.company_cache.add(company)
        self.stats['companies'] += 1
        return company

    def escape_string(self, s: str) -> str:
        """Escape special characters for Gremlin query"""
        if not s:
            return ""
        return s.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ').replace('\r', '')

    def add_movie_vertex(self, row: Dict) -> bool:
        """Add a Movie vertex with all its relationships"""
        try:
            movie_id = self.escape_string(row['imdb_title_id'])
            title = self.escape_string(row['original_title'])
            year = row['year']
            duration = row['duration']
            description = self.escape_string(row['description'])
            avg_vote = row['avg_vote']
            votes = row['votes']

            # Create Movie vertex
            query = (
                "g.addV('Movie')"
                f".property('id', '{movie_id}')"
                ".property('pk', 'Movie')"            # <-- partition key
                f".property('title', '{title}')"
                f".property('year', {year})"
                f".property('duration', {duration})"
                f".property('description', '{description}')"
                f".property('avg_vote', {avg_vote})"
                f".property('votes', {votes})"
            )
            self.execute_query(query)
            self.stats['movies'] += 1

            # Add director relationship
            if row['director']:
                director = self.add_person_vertex(row['director'])
                director_escaped = self.escape_string(director)
                query = (
                    f"g.V('{director_escaped}').addE('DIRECTED')"
                    f".to(g.V('{movie_id}'))"
                )
                self.execute_query(query)
                self.stats['directed'] += 1

            # Add actors relationships
            if row['actors']:
                actors = [a.strip() for a in row['actors'].split(',')]
                for actor in actors:
                    if actor:
                        actor_name = self.add_person_vertex(actor)
                        actor_escaped = self.escape_string(actor_name)
                        query = (
                            f"g.V('{actor_escaped}').addE('ACTED_IN')"
                            f".to(g.V('{movie_id}'))"
                        )
                        self.execute_query(query)
                        self.stats['acted_in'] += 1

            # Add writer relationships
            if row['writer']:
                writers = [w.strip() for w in row['writer'].split(',')]
                for writer in writers:
                    if writer:
                        writer_name = self.add_person_vertex(writer)
                        writer_escaped = self.escape_string(writer_name)
                        query = (
                            f"g.V('{writer_escaped}').addE('WROTE')"
                            f".to(g.V('{movie_id}'))"
                        )
                        self.execute_query(query)
                        self.stats['wrote'] += 1

            # Add genre relationships
            if row['genre']:
                genres = [g.strip() for g in row['genre'].split(',')]
                for genre in genres:
                    if genre:
                        genre_name = self.add_genre_vertex(genre)
                        genre_escaped = self.escape_string(genre_name)
                        query = (
                            f"g.V('{movie_id}').addE('HAS_GENRE')"
                            f".to(g.V('{genre_escaped}'))"
                        )
                        self.execute_query(query)
                        self.stats['has_genre'] += 1

            # Add production company relationship
            if row['production_company']:
                company = self.add_company_vertex(row['production_company'])
                company_escaped = self.escape_string(company)
                query = (
                    f"g.V('{movie_id}').addE('PRODUCED_BY')"
                    f".to(g.V('{company_escaped}'))"
                )
                self.execute_query(query)
                self.stats['produced_by'] += 1

            return True

        except Exception as e:
            print(f"Error adding movie {row.get('original_title', 'unknown')}: {e}")
            return False

    def import_csv(self, clear_existing: bool = False):
        """Import all movies from CSV file"""
        if clear_existing:
            confirm = input("Are you sure you want to clear all existing data? (yes/no): ")
            if confirm.lower() == 'yes':
                self.clear_graph()
            else:
                print("Skipping clear operation")

        print(f"Reading CSV file: {self.csv_file_path}")

        with open(self.csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader, 1):
                print(f"Processing movie {i}: {row['original_title']}")
                self.add_movie_vertex(row)

                # Progress update every 10 movies
                if i % 10 == 0:
                    print(f"  Processed {i} movies...")

        print("\n" + "="*50)
        print("Import Complete!")
        print("="*50)
        print(f"Movies imported: {self.stats['movies']}")
        print(f"People created: {self.stats['people']}")
        print(f"Genres created: {self.stats['genres']}")
        print(f"Companies created: {self.stats['companies']}")
        print(f"ACTED_IN edges: {self.stats['acted_in']}")
        print(f"DIRECTED edges: {self.stats['directed']}")
        print(f"WROTE edges: {self.stats['wrote']}")
        print(f"HAS_GENRE edges: {self.stats['has_genre']}")
        print(f"PRODUCED_BY edges: {self.stats['produced_by']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_movies.py <csv_file_path> [--clear]")
        print("  --clear: Clear all existing data before import")
        sys.exit(1)

    csv_file = sys.argv[1]
    clear_existing = '--clear' in sys.argv

    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)

    importer = MovieGraphImporter(csv_file)

    try:
        importer.connect()
        importer.import_csv(clear_existing=clear_existing)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
