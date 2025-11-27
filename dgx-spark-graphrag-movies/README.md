# CineGraph - Movie GraphRAG Application

CineGraph is an AI-powered movie query application that uses Neo4j GraphRAG to index and query movie entities and relationships. Users can ask questions about movies, actors, directors, writers, and genres through a Next.js web interface, receiving natural language responses.

Note: This app is a quick demo, and has been built for clarity and education purposes. It is not tuned or hardened for production deployment.

## Architecture

The application consists of 4 microservices orchestrated via Docker Compose:

1. **Neo4j** - Graph database storing movie entities and relationships
2. **vLLM** - LLM inference server running Llama 3.1 8B
3. **Python Backend API** - FastAPI service handling GraphRAG queries and CSV import
4. **Next.js Frontend** - Chat UI for user interactions

## Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with CUDA support (for vLLM)
- NVIDIA Container Toolkit installed
- At least 16GB GPU memory (for Llama 3.1 8B)

## Project Structure

```
graphrag_movies/
├── docker-compose.yml          # Service orchestration
├── backend/
│   ├── Dockerfile              # Backend container definition
│   ├── requirements.txt        # Python dependencies
│   ├── movies.csv              # Input CSV file (250 movies)
│   └── app/
│       ├── main.py             # FastAPI application
│       ├── database.py         # Neo4j connection & operations
│       ├── csv_importer.py     # CSV parsing & graph population
│       ├── graphrag.py         # GraphRAG query implementation
│       └── llm_client.py       # vLLM API client
└── frontend/
    ├── Dockerfile              # Frontend container definition
    ├── package.json            # Node.js dependencies
    ├── next.config.js          # Next.js configuration
    └── src/
        ├── app/
        │   ├── page.tsx        # Main chat interface
        │   └── api/chat/route.ts  # API route proxy
        └── components/
            └── ChatInterface.tsx   # Chat UI component
```

## Graph Schema

### Nodes
- **Movie**: imdb_title_id, original_title, year, duration, description, avg_vote, votes
- **Person**: name (for actors, directors, writers)
- **Genre**: name
- **ProductionCompany**: name

### Relationships
- `ACTED_IN` (Person → Movie)
- `DIRECTED` (Person → Movie)
- `WROTE` (Person → Movie)
- `HAS_GENRE` (Movie → Genre)
- `PRODUCED_BY` (Movie → ProductionCompany)

## Setup Instructions

1. **Place the CSV file**: Ensure `backend/movies.csv` exists with your movie data. The CSV should have the following columns:
   - imdb_title_id, original_title, year, genre, duration, director, writer, production_company, actors, description, avg_vote, votes

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Wait for services to initialize**:
   - Neo4j will start and be ready on port 7474 (HTTP) and 7687 (Bolt)
   - vLLM will download the Llama 3.1 8B model on first run (this may take several minutes)
   - Backend will automatically import CSV data if the graph is empty
   - Frontend will be available on port 3000

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Neo4j Browser: http://localhost:7474 (neo4j/cinegraph123)

## Usage Examples

The application supports various types of queries:

### Actor and Genre Queries
- "Which Crime movies is Joe Pesci in?"

### Director and Actor Queries
- "Which films directed by Christopher Nolan was Christian Bale in?"

### General Queries
- "What movies are about Frodo?"

## API Endpoints

### POST /api/chat
Submit a question and receive a natural language response.

**Request:**
```json
{
  "question": "What SciFi movies star Keanu Reeves?"
}
```

**Response:**
```json
{
  "answer": "Well, let me tell you about some fantastic SciFi films...",
  "movies_found": 3
}
```

### GET /api/health
Check the health status of all services.

**Response:**
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "vllm_available": true,
  "graph_has_data": true
}
```

## Configuration

### Environment Variables

**Backend:**
- `NEO4J_URI`: Neo4j connection URI (default: neo4j://neo4j:7687)
- `NEO4J_USER`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password (default: cinegraph123)
- `VLLM_API_URL`: vLLM API endpoint (default: http://vllm:8000/v1)
- `CSV_PATH`: Path to movies CSV file (default: /app/movies.csv)

**Frontend:**
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

1. **vLLM fails to start**: Ensure you have NVIDIA GPU drivers and Docker GPU support configured. Check with `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`

2. **Neo4j connection errors**: Wait for Neo4j to fully initialize (check health endpoint). Default credentials are neo4j/cinegraph123.

3. **CSV import not working**: Verify the CSV file exists at `backend/movies.csv` and has the correct format. Check backend logs for import errors.

4. **Frontend can't reach backend**: Ensure both services are on the same Docker network. Check `NEXT_PUBLIC_API_URL` environment variable.

## Technical Stack

- **Backend**: Python 3.11+, FastAPI, neo4j-driver, pandas, httpx
- **Frontend**: Next.js 14+, TypeScript, React
- **Database**: Neo4j 5.15
- **LLM**: vLLM with Llama 3.1 8B Instruct
- **Orchestration**: Docker Compose

## License

This project is provided as-is for demonstration purposes.

