from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import chromadb
import os

# === Config ===
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "/data/chroma")
COLLECTION_NAME = "image_vectors"
VECTOR_DIM = 768  # <-- openai/clip-vit-large-patch14 stored vectors are 768-dimensional

# === Chroma client & collection ===
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

app = FastAPI(title="Vector DB API (Chroma)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://doc:3000"],
    allow_credentials=True,
    allow_methods=["*"],          # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)


# === Request / Response models ===
class VectorItem(BaseModel):
    id: str = Field(..., description="Unique ID for the vector (e.g., image id)")
    vector: List[float] = Field(..., description="Embedding vector")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")

class UpsertRequest(BaseModel):
    vectors: List[VectorItem]

class SearchRequest(BaseModel):
    query_vector: List[float]
    top_k: int = 5
    where: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metadata filter"
    )

class SearchResult(BaseModel):
    id: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]

class VectorsResponse(BaseModel):
    vectors: List[VectorItem]
    count: int

@app.get("/health")
def health():
    return {
        "status": "ok",
        "db_path": CHROMA_DB_PATH,
        "collection": COLLECTION_NAME,
    }

# === Upsert vectors ===
@app.post("/v1/vectors")
def upsert_vectors(req: UpsertRequest):
    if not req.vectors:
        raise HTTPException(status_code=400, detail="No vectors provided")

    ids = []
    embeddings = []
    metadatas = []

    for item in req.vectors:
        if len(item.vector) != VECTOR_DIM:
            raise HTTPException(
                status_code=400,
                detail=f"Vector dimension mismatch. Expected {VECTOR_DIM}, got {len(item.vector)} (id={item.id})",
            )
        ids.append(item.id)
        embeddings.append(item.vector)
        metadatas.append(item.metadata or {})

    collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
    return {"status": "ok", "upserted": len(ids)}

# === Search vectors ===
@app.post("/v1/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if len(req.query_vector) != VECTOR_DIM:
        raise HTTPException(
            status_code=400,
            detail=f"Vector dimension mismatch. Expected {VECTOR_DIM}, got {len(req.query_vector)}",
        )

    res = collection.query(
        query_embeddings=[req.query_vector],
        n_results=req.top_k
    )

    # Chroma returns dicts with lists
    ids = res.get("ids", [[]])[0]
    dists = res.get("distances", [[]])[0]  # lower is closer, usually
    metadatas = res.get("metadatas", [[]])[0]

    results = []
    for _id, dist, meta in zip(ids, dists, metadatas):
        # Convert distance to a score (you can customize this)
        score = float(dist)
        results.append(
            SearchResult(
                id=_id,
                score=score,
                metadata=meta,
            )
        )

    return SearchResponse(results=results)

# === Get first n vectors ===
@app.get("/v1/vectors", response_model=VectorsResponse)
def get_vectors(n: int = 3):
    """
    Get the first n vectors from the database.
    
    Args:
        n: Number of vectors to retrieve (default: 3)
    
    Returns:
        List of vectors with their IDs, embeddings, and metadata
    """
    if n < 1:
        raise HTTPException(status_code=400, detail="n must be at least 1")
    
    # Get the first n vectors from ChromaDB
    results = collection.get(limit=n, include=['embeddings', 'metadatas'])
    
    ids = results.get("ids", [])
    embeddings = results.get("embeddings", [])
    metadatas = results.get("metadatas", [])
    
    vectors = []
    for _id, embedding, metadata in zip(ids, embeddings, metadatas):
        vectors.append(
            VectorItem(
                id=_id,
                vector=embedding,
                metadata=metadata if metadata else None
            )
        )
    
    return VectorsResponse(vectors=vectors, count=len(vectors))

# === Delete a single vector by id ===
@app.delete("/v1/vectors/{vector_id}")
def delete_vector(vector_id: str):
    collection.delete(ids=[vector_id])
    return {"status": "ok", "deleted_id": vector_id}

# === Clear all vectors ===
@app.delete("/v1/vectors")
def clear_all_vectors():
    global collection

    # Delete the collection and all vectors
    client.delete_collection(COLLECTION_NAME)

    # Recreate and rebind the global handle
    collection = client.get_or_create_collection(COLLECTION_NAME)

    return {"status": "ok", "cleared": True, "collection_reset": True}