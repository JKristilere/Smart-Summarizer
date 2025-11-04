"""Retrieve and Summarize texts based on similarity search in vector store."""

from app.embeddings.vectorstore import VectorStore
from app.utils import extract_video_id
from app.db import DBManager
from app.db.models import ChatHistory
from app.schema import ChatHistorySchema
from groq import Groq
from config import settings
from datetime import datetime, timezone

groq_api_key = settings.GROQ_API_KEY
db_manager = DBManager(settings.DATABASE_URI)

class RetrievalManager:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.groq_client = Groq(api_key=groq_api_key)

    def summarize_youtube_video(self, video_url: str):
        """
        Summarizes the video based on the url link
        """
        video_id = extract_video_id(video_url)
        results = self.vector_store.query_by_metadata({"video_id":video_id})
        context = "\n\n".join(results)
        prompt=f"""
                Generate a well detailed summary of the youtube using the following context:\n\n{context}\n\n
                Summary:
                """
        reponse = self.groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", 
                 "content": "You are a helpful assistant that summarizes text based on the provided context."
                 },
                {"role": "user", 
                 "content": prompt}
            ],
        )

        db_manager.insert_data(ChatHistory, ChatHistorySchema(message=reponse.choices[0].message.content, role="user"))
        return reponse.choices[0].message.content
    
    def summarize_audio_file(self, file_id:str):
        results = self.vector_store.query_by_metadata({"file_id": file_id})
        context = "\n\n".join(results)
        prompt=f"""
                Generate a well detailed summary of the audio transcript using the following context:\n\n{context}\n\n
                Summary:
                """
        reponse = self.groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", 
                 "content": "You are a helpful assistant that summarizes text based on the provided context."
                 },
                {"role": "user", 
                 "content": prompt}
            ],
        )
        db_manager.insert_data(ChatHistory, ChatHistorySchema(message=reponse.choices[0].message.content, role="user"))
        return reponse.choices[0].message.content
    

    def search_and_summarize(self, query: str, top_k: int = 5):
        """
        Retrieves and summarizes texts to the query from the vector store, with chat history for context.
        """
        results = self.vector_store.query(query_text=query, top_k=top_k)
        context = "\n\n".join(results)
        if not context:
            return "No relevant information found."
        
        # Prepare messages for the LLM, including chat history if provided
        messages = [
            {"role": "system", 
             "content": "You are a helpful assistant that summarizes text based on the user's query and provided context."
            },
            {"role": "user", 
            "content": f"Summarize the following context for the query: '{query}'\n\nContext:\n{context}\n\nSummary:"}
        ]
        
        reponse = self.groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
        )

        # Add the response to the conversations table
        chat_history = ChatHistorySchema(query=query, 
                                         message=reponse.choices[0].message.content, 
                                         role="user",
                                         created_at=datetime.now(timezone.utc))
        
        db_manager.insert_data(model=ChatHistory, data=chat_history)


        return reponse.choices[0].message.content
    
