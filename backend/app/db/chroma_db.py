import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from fastapi import Depends
from config import settings
import os

_client: ClientAPI | None = None
_collection: Collection | None = None

def get_chroma_client() -> ClientAPI:
    """Get or create ChromaDB cloud client with proper error handling."""
    global _client
    if _client is None:
        # Get credentials from config/settings
        api_key = settings.CHROMA_API_KEY
        tenant = settings.CHROMA_TENANT
        database = settings.CHROMA_DATABASE
        
        # Validate credentials exist
        if not api_key:
            raise ValueError("CHROMA_API_KEY environment variable is not set")
        if not tenant:
            raise ValueError("CHROMA_TENANT environment variable is not set")
        if not database:
            raise ValueError("CHROMA_DATABASE environment variable is not set")
        
        print(f"🔌 Connecting to ChromaDB Cloud...")
        print(f"   Tenant: {tenant}")
        print(f"   Database: {database}")
        print(f"   API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '****'}")
        
        try:
            _client = chromadb.CloudClient(
                api_key=api_key,
                tenant=tenant,
                database=database
            )
            print("✅ ChromaDB connection established!")
        except Exception as e:
            print(f"❌ Failed to connect to ChromaDB: {e}")
            raise ValueError(f"ChromaDB connection failed: {e}")
    
    return _client

def get_chroma_collection(
    client: ClientAPI = Depends(get_chroma_client)
) -> Collection:
    """Get or create ChromaDB collection."""
    global _collection
    if _collection is None:
        try:
            _collection = client.get_or_create_collection(
                name="my_collection",
            )
            print(f"✅ Collection 'my_collection' ready")
        except Exception as e:
            print(f"❌ Failed to get/create collection: {e}")
            raise ValueError(f"Collection setup failed: {e}")
    
    return _collection

def verify_chroma_connection():
    """Test ChromaDB connection - useful for debugging."""
    try:
        client = get_chroma_client()
        # Try to list collections as a connection test
        collections = client.list_collections()
        print(f"✅ ChromaDB verified. Found {len(collections)} collections.")
        return True
    except Exception as e:
        print(f"❌ ChromaDB verification failed: {e}")
        return False