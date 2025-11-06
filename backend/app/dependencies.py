from functools import lru_cache
from config import get_settings, Settings
from app.db import DBManager
from fastapi import Depends
from typing import Annotated
from app.ingestion import IngestionManager
from app.retriever import RetrievalManager
from app.embeddings import EmbeddingManager
from app.embeddings.vectorstore import VectorStore


_db_manager = None
_embedding_manager = None
_ingestion_manager = None


def get_db_manager(
        settings: Annotated[Settings, Depends(get_settings)]
):
    global _db_manager
    if _db_manager is None:
        _db_manager = DBManager(db_url=settings.DATABASE_URI)
    return _db_manager


def get_ingestion_manager():
    global _ingestion_manager
    if _ingestion_manager is None:
        _ingestion_manager = IngestionManager()
    return _ingestion_manager

def get_embedding_manager():
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager 

def get_vector_store(embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)]):
    return VectorStore(embedding_manager=embedding_manager)

def get_retrieval_manager(vector_store: Annotated[VectorStore, Depends(get_vector_store)]):
    return RetrievalManager(vector_store=vector_store)

   

