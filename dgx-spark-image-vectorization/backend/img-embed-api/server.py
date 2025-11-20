from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoProcessor, AutoModel
from typing import List, Optional
from PIL import Image
import torch
import io
import os
import base64
import requests

MODEL_ID = "openai/clip-vit-large-patch14"
hf_token = os.environ.get("HF_TOKEN")

app = FastAPI(title="EVL Image Embedding Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://doc:3000"],
    allow_credentials=True,
    allow_methods=["*"],          # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

print("Loading model:", MODEL_ID)
device = "cuda" if torch.cuda.is_available() else "cpu"

processor = AutoProcessor.from_pretrained(MODEL_ID, token=hf_token)
model = AutoModel.from_pretrained(MODEL_ID, dtype=torch.float16, token=hf_token)
model.to(device)
model.eval()

class EmbeddingRequest(BaseModel):
  # you can support either a single image or a batch of image URLs
  image_urls: Optional[List[str]] = None
  image_base64: Optional[List[str]] = None

class EmbeddingResponse(BaseModel):
  embeddings: List[List[float]]

def load_image_from_url(url: str) -> Image.Image:
  resp = requests.get(url)
  if not resp.ok:
    raise HTTPException(status_code=400, detail=f"Failed to fetch image: {url}")
  return Image.open(io.BytesIO(resp.content)).convert("RGB")

def load_image_from_b64(b64: str) -> Image.Image:
  data = base64.b64decode(b64)
  return Image.open(io.BytesIO(data)).convert("RGB")

@app.get("/health")
def health():
  return {"status": "ok", "model": MODEL_ID}

@app.post("/v1/embeddings", response_model=EmbeddingResponse)
def create_embeddings(req: EmbeddingRequest):
  images = []

  if req.image_urls:
    for url in req.image_urls:
      images.append(load_image_from_url(url))

  if req.image_base64:
    for b64 in req.image_base64:
      images.append(load_image_from_b64(b64))

  if not images:
    raise HTTPException(status_code=400, detail="No images provided")

  inputs = processor(images=images, return_tensors="pt").to(device)
  with torch.no_grad():
    image_features = model.get_image_features(**inputs)

  # Normalize embeddings
  image_features = torch.nn.functional.normalize(image_features, p=2, dim=-1)
  embeddings = image_features.cpu().tolist()

  return EmbeddingResponse(embeddings=embeddings)