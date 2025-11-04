"""Generate embeddings for text using SentenceTransformers."""

from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    
    def create_embeddings(self, documents: List[str]):
        try:
            embeddings = self.model.encode(documents)
            return embeddings
        except Exception as e:
            raise RuntimeError(f"Failed to create embeddings: {e}")
