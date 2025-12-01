"""
MCP (Model Context Protocol) Handler
Handles MCP protocol methods and tool definitions
"""

from typing import Dict, List, Any


class MCPHandler:
    """Handles MCP protocol interactions"""

    def __init__(self):
        self.server_info = {
            "name": "movie-graph-mcp",
            "version": "1.0.0"
        }

        # Define MCP tools
        self.tools = [
            {
                "name": "find_movies_by_actor_director",
                "description": "Find movies where a specific actor worked with a specific director. Uses partial name matching (e.g., 'Freeman' matches 'Morgan Freeman').",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "actor": {
                            "type": "string",
                            "description": "Actor name or partial name (e.g., 'Morgan Freeman' or 'Freeman')"
                        },
                        "director": {
                            "type": "string",
                            "description": "Director name or partial name (e.g., 'Christopher Nolan' or 'Nolan')"
                        }
                    },
                    "required": ["actor", "director"]
                }
            },
            {
                "name": "find_movies_by_actor_genre",
                "description": "Find movies where a specific actor acted in movies of a specific genre. Uses partial name matching for actor names.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "actor": {
                            "type": "string",
                            "description": "Actor name or partial name (e.g., 'Tom Hanks' or 'Hanks')"
                        },
                        "genre": {
                            "type": "string",
                            "description": "Genre name (e.g., 'Drama', 'Action', 'Comedy')"
                        }
                    },
                    "required": ["actor", "genre"]
                }
            },
            {
                "name": "find_movies_by_actor_director_genre",
                "description": "Find movies where a specific actor acted in movies of a specific genre that were directed by a specific director. Uses partial name matching for people names.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "actor": {
                            "type": "string",
                            "description": "Actor name or partial name"
                        },
                        "director": {
                            "type": "string",
                            "description": "Director name or partial name"
                        },
                        "genre": {
                            "type": "string",
                            "description": "Genre name (e.g., 'Drama', 'Action', 'Crime')"
                        }
                    },
                    "required": ["actor", "director", "genre"]
                }
            },
            {
                "name": "find_movies_by_genre_keywords",
                "description": "Find movies within a specific genre that contain given keywords in the movie description. Uses case-insensitive substring matching.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "genre": {
                            "type": "string",
                            "description": "Genre name (e.g., 'Drama', 'Sci-Fi', 'Thriller')"
                        },
                        "keywords": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of keywords to search for in movie descriptions (e.g., ['prison', 'redemption'])"
                        }
                    },
                    "required": ["genre"]
                }
            }
        ]

    def handle_initialize(self, params: Dict[str, Any]) -> Dict:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": self.server_info,
            "capabilities": {
                "tools": {}
            }
        }

    def handle_tools_list(self) -> Dict:
        """Handle MCP tools/list request"""
        return {
            "tools": self.tools
        }
