"""Store embeddings in a vector store and perform similarity search."""
import chromadb
import numpy as np
from app.db import DBManager
from app.embeddings import EmbeddingManager
from app.schema import YoutubeStoreSchema, AudioStoreSchema
from app.db.models import Youtube, Audio
from app.utils import extract_video_id
import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone
from config import settings

CHROMA_API_KEY =  settings.CHROMA_API_KEY
CHROMA_TENANT_ID =  settings.CHROMA_TENANT
CHROMA_DATABASE = settings.CHROMA_DATABASE
db_manager = DBManager(settings.DATABASE_URI)

class VectorStore:
    def __init__(self,
                 collection_name: str = "youtube_embeddings",
                 embedding_manager: EmbeddingManager = None):
        self.embedding_manager = embedding_manager
        self.collection_name = collection_name
        self.client = chromadb.CloudClient(
            api_key=CHROMA_API_KEY,
            tenant=CHROMA_TENANT_ID,
            database=CHROMA_DATABASE
        )
        # try:
            # Try to get existing collection first
        self.collection = self.client.get_collection(self.collection_name)
        # except Exception:
        #     # If collection doesn't exist, create it
        #     self.collection = self.client.create_collection(self.collection_name)

    def add_youtube_documents(self, documents: List[Any], embeddings: List[np.ndarray]):
        """Adds documents and their embeddings to the vector store."""

        if len(documents) !=  len(embeddings):
            raise ValueError("The number of documents must match the number of embeddings.")
        
        # Prepare data for ChromaDB
        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            # Generate unique ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(doc_id)
            
            # Prepare metadata
            metadata = dict(doc.metadata)
            metadata['doc_index'] = i
            metadata['content_length'] = len(doc.page_content)
            metadata["video_id"]= extract_video_id(doc.metadata["source"])
            metadatas.append(metadata)
            
            # Document content
            documents_text.append(doc.page_content)
            
            # Embedding
            embeddings_list.append(embedding)
        
        # Add to collection
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents_text
            )
            
            # Add to database
            data = YoutubeStoreSchema(url=doc.metadata["source"], 
                                      video_id=metadata["video_id"], 
                                      content=doc.page_content, 
                                      created_at=datetime.now(timezone.utc))
            
            db_manager.insert_data(Youtube, data)

            print(f"Successfully added {len(documents)} documents to vector store")
            print(f"Total documents in collection: {self.collection.count()}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to add documents to vector store: {e}")
    

    def add_audio_documents(self, filename: str, documents: List[Any], embeddings: List[np.ndarray]):
        """Adds documents and their embeddings to the vector store."""
        if len(documents) !=  len(embeddings):
            raise ValueError("The number of documents must match the number of embeddings.")
        
        # Prepare data for ChromaDB
        file_id = filename + uuid.uuid4().hex[:4]
        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []

        for doc, embedding in zip(documents, embeddings):
            # Generate unique ID
            created_at = datetime.now(timezone.utc)
            doc_id = f"doc_{uuid.uuid4().hex[:8]}"
            ids.append(doc_id)

            # Prepare metadata
            metadata = {
                "doc_index": documents.index(doc),
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
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents_text
            )

            # Add to database
            data = AudioStoreSchema(file_id=file_id, 
                                    content=doc, 
                                    created_at=created_at)
            
            db_manager.insert_data(Audio, data)

            print(f"Successfully added {len(documents)} documents to vector store")
            print(f"Total documents in collection: {self.collection.count()}")

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
        results = self.collection.get(
            where=metadata_filter
            )
        return results['documents']
        # return results
    
    def clear_collection(self) -> None:
        """Clear all data from the collection."""
        self.collection.delete(ids=self.collection.get()['ids'])
        print(f"Cleared all data from collection '{self.collection_name}'")
    
    def delete_data(self, filter):
        """Remove data based on the filter provided."""
        try:
            self.collection.delete(
            where=filter
        )
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