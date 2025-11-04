from config import get_settings, Settings
from app.db import DBManager
from fastapi import Depends
from typing import Annotated
from app.ingestion import IngestionManager
from app.retriever import RetrievalManager
from app.embeddings import EmbeddingManager
from app.embeddings.vectorstore import VectorStore

def get_db_manager(
        settings: Annotated[Settings, Depends(get_settings)]
):
    return DBManager(db_url=settings.DATABASE_URI)


def get_ingestion_manager():
    return IngestionManager()

def get_embedding_manager():
    return EmbeddingManager() 

def get_vector_store(embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)]):
    return VectorStore(embedding_manager=embedding_manager) #, collection_name="youtube_embeddings")

def get_retrieval_manager(vector_store: Annotated[VectorStore, Depends(get_vector_store)]):
    return RetrievalManager(vector_store=vector_store)

   

