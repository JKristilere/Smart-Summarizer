"""Main application module for the Summarizer backend."""
from app.dependencies import (get_db_manager, get_embedding_manager, 
                              get_ingestion_manager, get_retrieval_manager, 
                              get_vector_store)
from config import get_settings


# Initialize settings
settings = get_settings()
