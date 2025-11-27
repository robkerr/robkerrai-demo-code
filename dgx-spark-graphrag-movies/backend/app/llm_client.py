"""vLLM API client for generating natural language responses."""
import os
import json
import httpx
import time
from typing import List, Dict, Any, Optional, Tuple


# SISKEL_EBERT_SYSTEM_PROMPT = """You are a movie critic duo like Siskel and Ebert, having a friendly conversation about movies. 
# When discussing films, respond in a conversational, engaging manner as if you're two critics sharing your thoughts.
# Be enthusiastic, opinionated, and knowledgeable. Reference specific details from the movies when relevant.
# Keep responses natural and conversational - imagine you're discussing these films over coffee.
# Format your response as if you're both speaking together, not as a formal review."""

SISKEL_EBERT_SYSTEM_PROMPT = f"""You are a research assistant that can answer questions about movies.
You are given a question and a list of movies.
You need to answer the question based on the movies.
You need to use the movies to answer the question.
You need to use the movies to answer the question.
"""

class VLLMClient:
    """Client for interacting with vLLM OpenAI-compatible API."""
    
    def __init__(self):
        self.api_url = os.getenv("VLLM_API_URL", "http://vllm:8001/v1")
        self.client = httpx.Client(timeout=60.0)
    
    def generate_response(self, question: str, graphrag_results: List[Dict[str, Any]]) -> Tuple[str, Dict[str, int], float]:
        """
        Generate a natural language response in Siskel & Ebert style.
        
        Args:
            question: The user's question
            graphrag_results: response from GraphRAG query
            
        Returns:
            Tuple of (response_text, token_usage_dict, elapsed_time)
            token_usage_dict contains: prompt_tokens, completion_tokens
        """
        start_time = time.time()
        
        if not graphrag_results:
            response_text = self._generate_no_results_response(question)
            elapsed_time = time.time() - start_time
            return response_text, {"prompt_tokens": 0, "completion_tokens": 0}, elapsed_time
        
        # Format movie results for the prompt
        groudning_text = self._format_grounding_data(graphrag_results)
        
        user_prompt = f"""User Question: {question}

Based on our movie database, here are the relevant films:

{groudning_text}

Please provide a text summary of the movies that are relevant to the user's question.
"""
        
        try:
            response = self.client.post(
                f"{self.api_url}/chat/completions",
                json={
                    "model": "nvidia/Llama-3.1-8B-Instruct-FP8",
                    "messages": [
                        {"role": "system", "content": SISKEL_EBERT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 500,
                    "stop": ["\n\n\n"]
                }
            )
            response.raise_for_status()
            result = response.json()
            elapsed_time = time.time() - start_time
            
            # Extract token usage from response
            usage = result.get("usage", {})
            token_usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0)
            }
            
            response_text = result["choices"][0]["message"]["content"].strip()
            return response_text, token_usage, elapsed_time
        except Exception as e:
            print(f"Error calling vLLM: {e}")
            # Fallback response
            elapsed_time = time.time() - start_time
            response_text = self._generate_fallback_response(question, movie_results)
            return response_text, {"prompt_tokens": 0, "completion_tokens": 0}, elapsed_time
    
    def _format_grounding_data(self, grounding_data: List[Dict[str, Any]]) -> str:
        """Format grounding data into a JSON string (list of JSON objects)."""
        # Limit to top 10 items
        limited_data = grounding_data[:100]
        # Convert list of dictionaries to JSON string
        return json.dumps(limited_data, indent=2)
    
    def _generate_no_results_response(self, question: str) -> str:
        """Generate a response when no movies are found."""
        return f"""Well, we've searched through our database, and unfortunately we couldn't find any movies that match "{question}". 

It's possible the films you're looking for aren't in our collection yet, or perhaps you're thinking of something we haven't indexed. 

Do you want to try rephrasing your question? We'd be happy to help you find something else!"""
    
    def _generate_fallback_response(self, question: str, movies: List[Dict[str, Any]]) -> str:
        """Generate a fallback response if LLM call fails."""
        if not movies:
            return self._generate_no_results_response(question)
        
        response_parts = [f"Great question! We found {len(movies)} movie(s) that match your query:\n\n"]
        
        for idx, movie in enumerate(movies[:5], 1):
            title = movie.get("title", "Unknown")
            year = movie.get("year", "?")
            rating = movie.get("rating", "?")
            response_parts.append(f"{idx}. {title} ({year}) - Rating: {rating}/10")
        
        response_parts.append("\nThese are some fantastic films worth checking out!")
        return "\n".join(response_parts)
    
    def analyze_query(self, question: str) -> Tuple[Dict[str, Any], Dict[str, int], float]:
        """
        Analyze a user's question to determine query type and extract key terms.
        
        Args:
            question: The user's question about movies
            
        Returns:
            Tuple of (analysis_dict, token_usage_dict, elapsed_time)
            analysis_dict contains query_type and extracted parameters:
            - query_type: one of "actor_genre", "keywords", "director_actor", "actor", "genre"
            - actor: actor name (if applicable)
            - genre: genre name (if applicable)
            - keywords: list of keywords (if applicable)
            - movie: movie title (if applicable)
            token_usage_dict contains: prompt_tokens, completion_tokens
        """
        start_time = time.time()
        analysis_prompt = f"""Analyze the following movie-related question and extract key information.

Question: "{question}"

Determine what type of search the user intends and extract the relevant key terms.

Query types:
1. "actor_genre" - User wants movies starring a specific actor in a specific genre    
3. "director_actor" - User wants movies by a director (identified via a movie) that also feature an actor
2. "keywords" - User wants movies matching keywords/themes in descriptions

Rules for query type determination:
If a name is found in the question, and the word 'director' *is not* in the question, then the name is an actor.
If a name is found in the question, and the word 'director' *is* in the question, then the name is a director.

Extract key terms:
- Actor and Director names: Extract full names (e.g., "Keanu Reeves", "Cillian Murphy")
- Genres: Extract genre names (e.g., "Sci-Fi", "Action", "Drama", "Comedy")
- Keywords: Extract important words/phrases for content-based search

Respond with a JSON object in this exact format:
{{
    "query_type": "one of the types above",
    "director": "director name or null",
    "actor": "actor name or null",
    "genre": "genre name or null",
    "keywords": ["list", "of", "keywords"] or null,
    "movie": "movie title or null"
}}

Only include fields that are relevant. Use null for fields that don't apply.
Be precise with actor names and genre names - use standard capitalization."""

        try:
            response = self.client.post(
                f"{self.api_url}/chat/completions",
                json={
                    "model": "nvidia/Llama-3.1-8B-Instruct-FP8",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that analyzes movie queries and extracts structured information. Always respond with valid JSON only."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    "temperature": 0.1,  # Low temperature for more consistent extraction
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"}  # Force JSON output
                }
            )
            response.raise_for_status()
            result = response.json()
            elapsed_time = time.time() - start_time
            
            # Extract token usage from response
            usage = result.get("usage", {})
            token_usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0)
            }
            
            content = result["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            analysis = json.loads(content)
            
            # Validate and normalize the response
            query_type = analysis.get("query_type", "keywords")
            if query_type not in ["actor_genre", "keywords", "director_actor", "actor", "genre"]:
                query_type = "keywords"
            
            # Build result dictionary
            result_dict = {"type": query_type}
            
            if analysis.get("actor"):
                result_dict["actor"] = analysis["actor"]
            if analysis.get("director"):
                result_dict["director"] = analysis["director"]

            if analysis.get("genre"):
                result_dict["genre"] = analysis["genre"]
            if analysis.get("keywords"):
                keywords = analysis["keywords"]
                if isinstance(keywords, list):
                    result_dict["keywords"] = keywords
                else:
                    result_dict["keywords"] = [keywords]
            if analysis.get("movie"):
                result_dict["movie"] = analysis["movie"]
            
            # If no specific terms extracted, fall back to keyword search
            if query_type == "keywords" and not result_dict.get("keywords"):
                result_dict["keywords"] = question.split()
                result_dict["description"] = question
            
            return result_dict, token_usage, elapsed_time
            
        except Exception as e:
            print(f"Error analyzing query with LLM: {e}")
            elapsed_time = time.time() - start_time
            # Fallback to keyword search if LLM fails
            fallback_dict = {
                "type": "keywords",
                "keywords": question.split(),
                "description": question
            }
            return fallback_dict, {"prompt_tokens": 0, "completion_tokens": 0}, elapsed_time
    
    def health_check(self) -> bool:
        """Check if vLLM service is healthy."""
        

        try:
            health_url = f"{self.api_url.replace('/v1', '')}/health"
            print(f"Health check: Calling URL: {health_url}")
            response = self.client.get(health_url, timeout=5.0)
            print(f"Health check: Response code: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check: Error calling URL: {health_url}")
            print(f"Health check: Error: {e}")
            return False


# Global client instance
llm_client = VLLMClient()

