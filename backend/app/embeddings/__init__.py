"""Generate embeddings for text using SentenceTransformers."""

from sentence_transformers import SentenceTransformer
from typing import List
from functools import lru_cache

_model_cache = {}   # Cache for loaded models

class EmbeddingManager:
    # Use smaller model for production with limited RAM
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):  # This is already small (~80MB)
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load model only when needed"""
        if self._model is None:
            if self.model_name not in _model_cache:
                print(f"Loading embedding model: {self.model_name}...")
                _model_cache[self.model_name] = SentenceTransformer(self.model_name)
                print(f"Embedding model loaded successfully!")
            self._model = _model_cache[self.model_name]
        return self._model
    
    @model.setter
    def model(self, value):
        self._model = value
    
    def create_embeddings(self, documents: List[str]):
        try:
            # Disable progress bar and batch encode to save memory
            embeddings = self.model.encode(
                documents, 
                show_progress_bar=False,
                batch_size=32  # Process in smaller batches
            )
            return embeddings
        except Exception as e:
            raise RuntimeError(f"Failed to create embeddings: {e}")

# """Generate embeddings for text using SentenceTransformers."""

# from sentence_transformers import SentenceTransformer
# from typing import List
# from functools import lru_cache

# _model_cache = {}   # Cache for loaded models

# class EmbeddingManager:
#     def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
#         self.model_name = model_name
#         self.model = None
    
#     @property
#     def model(self):
#         """Lazy load model only when needed"""
#         if self._model is None:
#             if self.model_name not in _model_cache:
#                 print(f"Loading embedding model: {self.model_name}...")
#                 _model_cache[self.model_name] = SentenceTransformer(self.model_name)
#                 print(f"Embedding model loaded successfully!")
#             self._model = _model_cache[self.model_name]
#         return self._model
    
    
    
#     @model.setter
#     def model(self, value):
#         self._model = value
    
#     def get_model(self):
#         if self._model is None:
#             if self.model_name not in _model_cache:
#                 print(f"Loading embedding model: {self.model_name}")
#                 _model_cache[self.model_name] = SentenceTransformer(self.model_name)
#             self._model = _model_cache[self.model_name]
#         return self._model
    
#     def create_embeddings(self, documents: List[str]):
#         try:
#             embeddings = self.model.encode(documents)
#             return embeddings
#         except Exception as e:
#             raise RuntimeError(f"Failed to create embeddings: {e}")
