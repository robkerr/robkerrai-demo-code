"""
Graph Query Functions for Cosmos DB Gremlin API
Implements movie search queries using Gremlin traversals
"""

import asyncio
import logging
from typing import List, Dict, Any
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError


class MovieGraphQueries:
    """Execute graph queries against Cosmos DB Gremlin API"""

    def __init__(self, endpoint: str, key: str, database: str, collection: str):
        self.endpoint = endpoint
        self.key = key
        self.database = database
        self.collection = collection
        self.gremlin_client = None
        self._connect()

    def _connect(self):
        """Establish connection to Cosmos DB Gremlin API"""
        try:
            logging.info(f"Connecting to Cosmos DB at {self.endpoint}")
            self.gremlin_client = client.Client(
                url=self.endpoint,
                traversal_source='g',
                username=f"/dbs/{self.database}/colls/{self.collection}",
                password=self.key,
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            logging.info("Connected to Cosmos DB successfully")
        except Exception as e:
            logging.error(f"Failed to connect to Cosmos DB: {e}")
            raise

    async def _execute_query(self, query: str) -> List:
        """Execute a Gremlin query and return results"""
        def _sync_execute():
            """Synchronous execution wrapper for running in thread pool"""
            callback = self.gremlin_client.submitAsync(query)
            result = callback.result()
            return result.all().result()

        try:
            logging.info(f"Executing query: {query}")
            # Run the blocking Gremlin calls in a thread pool to avoid event loop conflicts
            results = await asyncio.to_thread(_sync_execute)
            return results
        except GremlinServerError as e:
            logging.error(f"Gremlin server error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            raise

    def _format_movie(self, movie_data: Dict) -> Dict[str, Any]:
        """Format movie data for response"""
        return {
            "id": movie_data.get('id'),
            "title": movie_data.get('title'),
            "year": movie_data.get('year'),
            "duration": movie_data.get('duration'),
            "description": movie_data.get('description'),
            "avg_vote": movie_data.get('avg_vote'),
            "votes": movie_data.get('votes')
        }

    async def find_by_actor_director(self, actor: str, director: str) -> List[Dict]:
        """
        Find movies where a specific actor worked with a specific director
        Uses partial name matching (case-insensitive)
        """
        # Escape single quotes in input
        actor_safe = actor.replace("'", "\\'")
        director_safe = director.replace("'", "\\'")

        # Gremlin query with partial matching using textContains
        # Find Person vertices where name contains the actor string
        # Then traverse to movies they acted in
        # Then check if those movies were directed by someone whose name contains the director string
        query = f"""
            g.V().hasLabel('Person')
             .has('name', containing('{actor_safe}'))
             .outE('ACTED_IN')
             .inV().hasLabel('Movie')
             .as('movie')
             .inE('DIRECTED')
             .outV().hasLabel('Person')
             .has('name', containing('{director_safe}'))
             .select('movie')
             .dedup()
             .project('id', 'title', 'year', 'duration', 'description', 'avg_vote', 'votes')
               .by('id')
               .by('title')
               .by('year')
               .by('duration')
               .by('description')
               .by('avg_vote')
               .by('votes')
        """

        try:
            results = await self._execute_query(query)
            return [self._format_movie(movie) for movie in results]
        except Exception as e:
            logging.error(f"Error in find_by_actor_director: {e}")
            return []

    async def find_by_actor_genre(self, actor: str, genre: str) -> List[Dict]:
        """
        Find movies where a specific actor acted in movies of a specific genre
        Uses partial name matching for actor (case-insensitive)
        """
        actor_safe = actor.replace("'", "\\'")
        genre_safe = genre.replace("'", "\\'")

        query = f"""
            g.V().hasLabel('Person')
             .has('name', containing('{actor_safe}'))
             .outE('ACTED_IN')
             .inV().hasLabel('Movie')
             .as('movie')
             .outE('HAS_GENRE')
             .inV().hasLabel('Genre')
             .has('name', containing('{genre_safe}'))
             .select('movie')
             .dedup()
             .project('id', 'title', 'year', 'duration', 'description', 'avg_vote', 'votes')
               .by('id')
               .by('title')
               .by('year')
               .by('duration')
               .by('description')
               .by('avg_vote')
               .by('votes')
        """

        try:
            results = await self._execute_query(query)
            return [self._format_movie(movie) for movie in results]
        except Exception as e:
            logging.error(f"Error in find_by_actor_genre: {e}")
            return []

    async def find_by_actor_director_genre(self, actor: str, director: str, genre: str) -> List[Dict]:
        """
        Find movies where an actor acted in movies of a specific genre directed by a specific director
        Uses partial name matching for people (case-insensitive)
        """
        actor_safe = actor.replace("'", "\\'")
        director_safe = director.replace("'", "\\'")
        genre_safe = genre.replace("'", "\\'")

        query = f"""
            g.V().hasLabel('Person')
             .has('name', containing('{actor_safe}'))
             .outE('ACTED_IN')
             .inV().hasLabel('Movie')
             .as('movie')
             .outE('HAS_GENRE')
             .inV().hasLabel('Genre')
             .has('name', containing('{genre_safe}'))
             .select('movie')
             .inE('DIRECTED')
             .outV().hasLabel('Person')
             .has('name', containing('{director_safe}'))
             .select('movie')
             .dedup()
             .project('id', 'title', 'year', 'duration', 'description', 'avg_vote', 'votes')
               .by('id')
               .by('title')
               .by('year')
               .by('duration')
               .by('description')
               .by('avg_vote')
               .by('votes')
        """

        try:
            results = await self._execute_query(query)
            return [self._format_movie(movie) for movie in results]
        except Exception as e:
            logging.error(f"Error in find_by_actor_director_genre: {e}")
            return []

    async def find_by_genre_keywords(self, genre: str, keywords: List[str]) -> List[Dict]:
        """
        Find movies within a specific genre that contain keywords in description
        Uses case-insensitive substring matching for keywords
        """
        genre_safe = genre.replace("'", "\\'")

        # Start with genre filter
        query = f"""
            g.V().hasLabel('Genre')
             .has('name', containing('{genre_safe}'))
             .inE('HAS_GENRE')
             .outV().hasLabel('Movie')
        """

        # Add keyword filters if provided
        if keywords and len(keywords) > 0:
            for keyword in keywords:
                keyword_safe = keyword.replace("'", "\\'")
                # Filter movies that have description containing the keyword
                query += f".has('description', containing('{keyword_safe}'))"

        # Project the results
        query += """
             .dedup()
             .project('id', 'title', 'year', 'duration', 'description', 'avg_vote', 'votes')
               .by('id')
               .by('title')
               .by('year')
               .by('duration')
               .by('description')
               .by('avg_vote')
               .by('votes')
        """

        try:
            results = await self._execute_query(query)
            return [self._format_movie(movie) for movie in results]
        except Exception as e:
            logging.error(f"Error in find_by_genre_keywords: {e}")
            return []

    def close(self):
        """Close the Gremlin client connection"""
        if self.gremlin_client:
            self.gremlin_client.close()
