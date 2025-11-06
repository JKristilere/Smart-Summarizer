"""Store embeddings in a vector store and perform similarity search."""
import chromadb
import numpy as np
from app.embeddings import EmbeddingManager
from app.schema import YoutubeStoreSchema, AudioStoreSchema
from app.db.models import Youtube, Audio
from app.utils import extract_video_id
import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone
from config import settings
from functools import lru_cache

CHROMA_API_KEY = settings.CHROMA_API_KEY
CHROMA_TENANT_ID = settings.CHROMA_TENANT
CHROMA_DATABASE = settings.CHROMA_DATABASE

# Remove global db_manager - will be passed as parameter
# db_manager = DBManager(settings.DATABASE_URI)

_chroma_client = None


@lru_cache(maxsize=1)
def get_chroma_client():
    return chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=CHROMA_TENANT_ID,
        database=CHROMA_DATABASE
    )


class VectorStore:
    def __init__(self,
                 collection_name: str = "youtube_embeddings",
                 embedding_manager: EmbeddingManager = None,
                 db_manager=None):  # Add db_manager parameter
        self.embedding_manager = embedding_manager
        self.collection_name = collection_name
        self.client = get_chroma_client()  # reuse singleton
        self.collection = self.client.get_collection(self.collection_name)
        self.db_manager = db_manager  # Store for use in methods

    def add_youtube_documents(self, documents: List[Any], embeddings: List[np.ndarray]):
        """Adds documents and their embeddings to the vector store."""
        if len(documents) != len(embeddings):
            raise ValueError("The number of documents must match the number of embeddings.")
        
        # Prepare data for ChromaDB
        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []
        
        # Get video_id once (all docs from same video)
        video_id = extract_video_id(documents[0].metadata["source"])
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            # Generate unique ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(doc_id)
            
            # Prepare metadata
            metadata = dict(doc.metadata)
            metadata['doc_index'] = i
            metadata['content_length'] = len(doc.page_content)
            metadata["video_id"] = video_id
            metadatas.append(metadata)
            
            # Document content
            documents_text.append(doc.page_content)
            
            # Embedding
            embeddings_list.append(embedding)
        
        # Add to collection
        try:
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents_text
            )
            
            # Add to database only if db_manager is provided
            if self.db_manager:
                # Store only once per video, not per chunk
                data = YoutubeStoreSchema(
                    url=documents[0].metadata["source"], 
                    video_id=video_id, 
                    content="\n\n".join(documents_text),  # Combine all chunks
                    created_at=datetime.now(timezone.utc)
                )
                
                self.db_manager.insert_data(Youtube, data)
            print(f"Successfully added {len(documents)} documents to vector store")
            print(f"Total documents in collection: {self.collection.count()}")
            return video_id
        
        except Exception as e:
            raise RuntimeError(f"Failed to add documents to vector store: {e}")
    
    def add_audio_documents(self, filename: str, documents: List[Any], embeddings: List[np.ndarray]):
        """Adds documents and their embeddings to the vector store."""
        if len(documents) != len(embeddings):
            raise ValueError("The number of documents must match the number of embeddings.")
        
        # Prepare data for ChromaDB
        file_id = filename + uuid.uuid4().hex[:4]
        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []
        created_at = datetime.now(timezone.utc)

        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            # Generate unique ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(doc_id)

            # Prepare metadata
            metadata = {
                "doc_index": i,
                "context_length": len(doc),
                "file_id": file_id
            }
            metadatas.append(metadata)

            # Document content
            documents_text.append(doc)

            # Embedding
            embeddings_list.append(embedding)

        # Add to collection
        try:
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents_text
            )

            # Add to database only if db_manager is provided
            if self.db_manager:
                data = AudioStoreSchema(
                    file_id=file_id, 
                    content="\n\n".join(documents_text),  # Combine all chunks
                    created_at=created_at
                )
                
                self.db_manager.insert_data(Audio, data)
            print(f"Successfully added {len(documents)} documents to vector store")
            print(f"Total documents in collection: {self.collection.count()}")
            return file_id


        except Exception as e:
            raise RuntimeError(f"Failed to add documents to vector store: {e}")

    def similarity_search(self, query_embedding: List[float], top_k: int = 5):
        """Search for the top_k most similar documents to the query embedding."""
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        return results['documents'][0]
    
    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Generate embedding for the query text and perform similarity search."""
        query_embedding = self.embedding_manager.create_embeddings([query_text])
        return self.similarity_search(query_embedding, top_k=top_k)
    
    def query_by_metadata(self, metadata_filter: Dict[str, Any]):
        """Query documents based on metadata filters."""
        results = self.collection.get(where=metadata_filter)
        return results['documents']
    
    def clear_collection(self) -> None:
        """Clear all data from the collection."""
        self.collection.delete(ids=self.collection.get()['ids'])
        print(f"Cleared all data from collection '{self.collection_name}'")
    
    def delete_data(self, filter):
        """Remove data based on the filter provided."""
        try:
            self.collection.delete(where=filter)
            print("Data deleted successfully")
        except Exception as e:
            raise ValueError(f"Error deleting data: {e}")
        

        

# class VectorStoreManager:
#     def __init__(self, collection_name: str = "summarizer_collection", embedding_manager: EmbeddingManager = None):
#         """Initialize the vector store manager and connect to ChromaDB."""
#         self.client = chromadb.CloudClient(
#             api_key=CHROMA_API_KEY,
#             tenant=CHROMA_TENANT_ID,
#             database=CHROMA_DATABASE,
#         )
#         self.collection = self.client.get_or_create_collection(name=collection_name)
#         self.embedding_manager = embedding_manager or EmbeddingManager()

#     def add_embeddings(self, documents: List[str], embeddings: List[np.ndarray]) -> None:
#         """Add embeddings and their corresponding texts to the vector store."""
#         ids = [str(uuid.uuid4()) for _ in documents]
#         self.collection.add(
#             ids=ids,
#             documents=documents,
#             embeddings=embeddings)
#         print(f"Added {len(documents)} documents to the vector store.")

#     def similarity_search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
#         """Search for the top_k most similar documents to the query embedding."""
#         results = self.collection.query(
#             query_embeddings=[query_embedding],
#             n_results=top_k
#         )
#         return results['documents'][0]
    
#     def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
#         """Generate embedding for the query text and perform similarity search."""
#         query_embedding = self.embedding_manager.generate_embeddings([query_text])[0]
#         return self.similarity_search(query_embedding, top_k=top_k)
    
#     def clear_collection(self) -> None:
#         """Clear all data from the collection."""
#         self.collection.delete(ids=self.collection.get()['ids'])