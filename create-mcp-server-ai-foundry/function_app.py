"""
Azure Function App for MCP (Model Context Protocol) Server
Provides movie search capabilities via Cosmos DB Gremlin API
"""

import azure.functions as func
import logging
import json
import os
from typing import Dict, Any
from mcp_handler import MCPHandler
from graph_queries import MovieGraphQueries

# Initialize Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Initialize MCP handler and graph queries
mcp_handler = MCPHandler()
graph_queries = MovieGraphQueries(
    endpoint=os.getenv('COSMOS_ENDPOINT'),
    key=os.getenv('COSMOS_KEY'),
    database=os.getenv('COSMOS_DATABASE', 'moviedb'),
    collection=os.getenv('COSMOS_COLLECTION', 'movies')
)


@app.route(route="mcp", methods=["GET", "POST", "OPTIONS"])
async def mcp_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main MCP endpoint supporting SSE (Server-Sent Events) transport

    GET: SSE endpoint for MCP communication
    POST: Handle MCP JSON-RPC requests
    OPTIONS: CORS preflight
    """
    logging.info(f'MCP endpoint called: {req.method} {req.url}')

    # Handle CORS preflight
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            status_code=204,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Accept',
                'Access-Control-Max-Age': '86400'
            }
        )

    # Handle SSE connection (GET request)
    if req.method == 'GET':
        return handle_sse_connection(req)

    # Handle JSON-RPC request (POST)
    if req.method == 'POST':
        return await handle_jsonrpc_request(req)

    return func.HttpResponse(
        "Method not allowed",
        status_code=405,
        headers={'Access-Control-Allow-Origin': '*'}
    )


def handle_sse_connection(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle SSE connection for MCP protocol
    Note: Azure Functions has limitations with long-lived SSE connections
    """
    # Send SSE response with endpoint information
    response_data = json.dumps({
        "jsonrpc": "2.0",
        "method": "endpoint",
        "params": {
            "endpoint": req.url.replace('/mcp', '/mcp'),
            "capabilities": {
                "tools": True
            }
        }
    })

    sse_message = f"data: {response_data}\n\n"

    return func.HttpResponse(
        sse_message,
        status_code=200,
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )


async def handle_jsonrpc_request(req: func.HttpRequest) -> func.HttpResponse:
    """Handle MCP JSON-RPC requests"""
    try:
        # Parse request body
        body = req.get_json()
        logging.info(f'Received JSON-RPC request: {body}')

        # Handle different MCP methods
        method = body.get('method')
        params = body.get('params', {})
        request_id = body.get('id')

        response = None

        if method == 'initialize':
            response = mcp_handler.handle_initialize(params)

        elif method == 'tools/list':
            response = mcp_handler.handle_tools_list()

        elif method == 'tools/call':
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})
            response = await handle_tool_call(tool_name, tool_args)

        else:
            response = {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

        # Build JSON-RPC response
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": request_id
        }

        if "error" in response:
            jsonrpc_response["error"] = response["error"]
        else:
            jsonrpc_response["result"] = response

        return func.HttpResponse(
            json.dumps(jsonrpc_response),
            status_code=200,
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        )

    except ValueError as e:
        logging.error(f'Invalid JSON: {e}')
        return func.HttpResponse(
            json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                },
                "id": None
            }),
            status_code=400,
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        )

    except Exception as e:
        logging.error(f'Error handling request: {e}')
        return func.HttpResponse(
            json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": None
            }),
            status_code=500,
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        )


async def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict:
    """Route tool calls to appropriate graph query functions"""
    try:
        if tool_name == 'find_movies_by_actor_director':
            actor = arguments.get('actor')
            director = arguments.get('director')
            if not actor or not director:
                return {
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameters: actor and director"
                    }
                }
            movies = await graph_queries.find_by_actor_director(actor, director)

        elif tool_name == 'find_movies_by_actor_genre':
            actor = arguments.get('actor')
            genre = arguments.get('genre')
            if not actor or not genre:
                return {
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameters: actor and genre"
                    }
                }
            movies = await graph_queries.find_by_actor_genre(actor, genre)

        elif tool_name == 'find_movies_by_actor_director_genre':
            actor = arguments.get('actor')
            director = arguments.get('director')
            genre = arguments.get('genre')
            if not actor or not director or not genre:
                return {
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameters: actor, director, and genre"
                    }
                }
            movies = await graph_queries.find_by_actor_director_genre(actor, director, genre)

        elif tool_name == 'find_movies_by_genre_keywords':
            genre = arguments.get('genre')
            keywords = arguments.get('keywords', [])
            if not genre:
                return {
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameter: genre"
                    }
                }
            movies = await graph_queries.find_by_genre_keywords(genre, keywords)

        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }

        # Return results in MCP format
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(movies, indent=2)
                }
            ]
        }

    except Exception as e:
        logging.error(f'Error executing tool {tool_name}: {e}')
        return {
            "error": {
                "code": -32603,
                "message": f"Error executing tool: {str(e)}"
            }
        }


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({"status": "healthy"}),
        status_code=200,
        headers={
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    )
