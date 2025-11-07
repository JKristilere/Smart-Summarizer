"""Retrieve and Summarize texts based on similarity search in vector store."""
from app.embeddings.vectorstore import VectorStore
from app.utils import extract_video_id
from app.db import DBManager
from app.db.models import ChatHistory
from app.schema import ChatHistorySchema
from groq import Groq
from ollama import Client
from config import settings
from datetime import datetime, timezone
from typing import List, Optional, AsyncGenerator

groq_api_key = settings.GROQ_API_KEY

class RetrievalManager:
    def __init__(self, vector_store: VectorStore, db_manager: DBManager = None):
        self.vector_store = vector_store
        self.groq_client = Groq(api_key=groq_api_key)
        self.ollama_client = Client(settings.OLLAMA_HOST,
                                    headers={'Authorization': 'Bearer ' + settings.OLLAMA_API_KEY})
        self.ollama_model = settings.OLLAMA_MODEL
        self.db_manager = db_manager

    def summarize_youtube_video(self, video_url: str):
        """
        Summarizes the video based on the url link
        """
        video_id = extract_video_id(video_url)
        results = self.vector_store.query_by_metadata({"video_id": video_id})
        context = "\n\n".join(results)
        
        prompt = f"""
            Generate a well-detailed summary of the YouTube video using the following context:

            {context}

            Please provide a comprehensive summary covering the main points and key takeaways.
            """
        messages = [
                {"role": "system", 
                 "content": "You are a helpful assistant that summarizes YouTube videos based on their transcripts."
                },
                {"role": "user", 
                 "content": prompt}
            ]
        

        # # Using Groq
        # response = self.groq_client.chat.completions.create(
        #     model="llama-3.3-70b-versatile",
        #     messages=messages,
        # )
        # summary = response.choices[0].message.content


        #Using Ollama
        response = self.ollama_client.chat(
                model = self.ollama_model,
                messages=messages
        )
        summary = response.message.content


        # Save to chat history if db_manager is available
        if self.db_manager:
            chat_entry = ChatHistorySchema(
                message=summary,
                role="assistant",
                file_id=video_id,
                created_at=datetime.now(timezone.utc)
            )
            self.db_manager.insert_data(ChatHistory, chat_entry)
        
        return summary
    
    def summarize_audio_file(self, file_id: str):
        """
        Summarizes the audio file based on file_id
        """
        results = self.vector_store.query_by_metadata({"file_id": file_id})
        context = "\n\n".join(results)
        
        prompt = f"""
                Generate a well-detailed summary of the audio transcript using the following context:

                {context}

                Please provide a comprehensive summary covering the main points and key takeaways.
                """
        
        messages = [
                {"role": "system", 
                 "content": "You are a helpful assistant that summarizes audio transcripts."
                },
                {"role": "user", 
                 "content": prompt}
            ]
        
        # # Using Groq
        # response = self.groq_client.chat.completions.create(
        #     model="llama-3.3-70b-versatile",
        #     messages=messages,
        # )
        
        # summary = response.choices[0].message.content

        ## Using Ollama
        response = self.ollama_client.chat(
                model = self.ollama_model,
                messages=messages
        )

        summary = response.message.content
        
        
        # Save to chat history if db_manager is available
        if self.db_manager:
            chat_entry = ChatHistorySchema(
                message=summary,
                role="assistant",
                file_id=file_id,
                created_at=datetime.now(timezone.utc)
            )
            self.db_manager.insert_data(ChatHistory, chat_entry)
        
        return summary

    def search_and_summarize(self, query: str, top_k: int = 5, file_id: Optional[str] = None):
        """
        Retrieves and summarizes texts based on the query from the vector store.
        """
        # results = self.vector_store.query(query_text=query, top_k=top_k)
        # context = "\n\n".join(results)
        
        full_context = ""
        if file_id:
            results = self.vector_store.query_by_metadata({"file_id": file_id})
            results_2 = self.vector_store.query(query_text=query, top_k=top_k)
            results.extend(results_2)
        else:
            results = self.vector_store.query(query_text=query, top_k=top_k)

        # Use a generator expression to build the context string
        full_context = "\n\n".join(result for result in results)
        if not full_context:
            return "No relevant information found."
        
        # Prepare messages for the LLM
        messages = [
            {"role": "system", 
             "content": "You are a helpful assistant that answers questions based on the provided context."
            },
            {"role": "user", 
             "content": f"Question: {query}\n\nContext:\n{full_context}\n\nPlease provide a detailed answer based on the context above."}
        ]
        

        ## Using Groq
        # response = self.groq_client.chat.completions.create(
        #     model="llama-3.3-70b-versatile",
        #     messages=messages,
        # )
        # answer = response.choices[0].message.content


        ## Using Ollama
        response = self.ollama_client.chat(
                model = self.ollama_model,
                messages=messages
        )
        answer = response.message.content


        # Save query and response to chat history if db_manager is available
        if self.db_manager:
            # Save user query
            user_entry = ChatHistorySchema(
                message=query,
                role="user",
                file_id=file_id,
                created_at=datetime.now(timezone.utc)
            )
            self.db_manager.insert_data(ChatHistory, user_entry)
            
            # Save assistant response
            assistant_entry = ChatHistorySchema(
                message=answer,
                role="assistant",
                file_id=file_id,
                created_at=datetime.now(timezone.utc)
            )
            self.db_manager.insert_data(ChatHistory, assistant_entry)

        return answer
    
    def get_chat_history(self, file_id: str, limit: int = 50) -> List[ChatHistory]:
        """
        Retrieve chat history for a specific file_id (video_id or audio file_id)
        """
        if not self.db_manager:
            return []
        
        try:
            history = self.db_manager.filter_data(
                ChatHistory,
                file_id=file_id
            )
            # Sort by created_at and limit
            history.sort(key=lambda x: x.created_at)
            return history[-limit:] if len(history) > limit else history
        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []
    
    def chat_with_context(
        self, 
        query: str, 
        file_id: str,
        include_vector_search: bool = True,
        top_k: int = 3
    ):
        """
        Chat with the LLM using both chat history and vector search context.
        
        Args:
            query: User's question
            file_id: video_id or audio file_id to maintain context
            include_vector_search: Whether to include vector search results
            top_k: Number of relevant chunks to retrieve
        """
        # Get chat history
        chat_history = self.get_chat_history(file_id)
        
        # Build messages array
        messages = [
            {"role": "system", 
             "content": """You are a helpful assistant that answers questions about a YouTube video or audio file. 
                        Use the conversation history and provided context to give accurate, detailed answers."""
            }
        ]
        
        # Add recent chat history (last 10 messages to avoid token limits)
        for chat in chat_history[-10:]:
            messages.append({
                "role": chat.role,
                "content": chat.message
            })
        
        # Add current query with optional vector search context
        if include_vector_search:
            # Search for relevant content
            results = self.vector_store.query_by_metadata({"file_id": file_id})
            if not results:
                # Try with video_id for YouTube videos
                results = self.vector_store.query_by_metadata({"video_id": file_id})
            
            if results:
                # Also do semantic search on the query
                semantic_results = self.vector_store.query(query_text=query, top_k=top_k)
                context = "\n\n".join(semantic_results)
                
                user_message = f"""Question: {query}
                                    Relevant Context:
                                    {context}
                                Please answer the question based on the context and our conversation history."""
            else:
                user_message = query
        else:
            user_message = query
        
        messages.append({"role": "user", "content": user_message})
        
        # Get response

        ## Using Groq
        # response = self.groq_client.chat.completions.create(
        #     model="llama-3.3-70b-versatile",
        #     messages=messages,
        # )
        
        # answer = response.choices[0].message.content

        ## Using Ollama
        response = self.ollama_client.chat(
                model = self.ollama_model,
                messages=messages
        )
        answer = response.message.content

        # Save to chat history
        if self.db_manager:
            # Save user query
            user_entry = ChatHistorySchema(
                message=query,
                role="user",
                file_id=file_id,
                created_at=datetime.now(timezone.utc)
            )
            self.db_manager.insert_data(ChatHistory, user_entry)
            
            # Save assistant response
            assistant_entry = ChatHistorySchema(
                message=answer,
                role="assistant",
                file_id=file_id,
                created_at=datetime.now(timezone.utc)
            )
            self.db_manager.insert_data(ChatHistory, assistant_entry)

        return answer
    
    async def chat_with_context_streaming(
        self, 
        query: str, 
        file_id: str,
        include_vector_search: bool = True,
        top_k: int = 3
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat responses with context (for real-time streaming in UI).
        
        Args:
            query: User's question
            file_id: video_id or audio file_id to maintain context
            include_vector_search: Whether to include vector search results
            top_k: Number of relevant chunks to retrieve
        """
        # Get chat history
        chat_history = self.get_chat_history(file_id)
        
        # Build messages array
        messages = [
            {"role": "system", 
             "content": "You are a helpful assistant that answers questions about a YouTube video or audio file. Use the conversation history and provided context to give accurate, detailed answers."
            }
        ]
        
        # Add recent chat history (last 10 messages)
        for chat in chat_history[-10:]:
            messages.append({
                "role": chat.role,
                "content": chat.message
            })
        
        # Add current query with optional vector search context
        if include_vector_search:
            # Search for relevant content
            results = self.vector_store.query_by_metadata({"file_id": file_id})
            if not results:
                results = self.vector_store.query_by_metadata({"video_id": file_id})
            
            if results:
                semantic_results = self.vector_store.query(query_text=query, top_k=top_k)
                context = "\n\n".join(semantic_results)
                
                user_message = f"""Question: {query}
                                Relevant Context:
                                {context}

                                Please answer the question based on the context and our conversation history."""
            else:
                user_message = query
        else:
            user_message = query
        
        messages.append({"role": "user", "content": user_message})
        
        # Get streaming response


        ## Using Groq
        # stream = self.groq_client.chat.completions.create(
        #     model="llama-3.3-70b-versatile",
        #     messages=messages,
        #     stream=True,
        # )
        
        # # Collect full response for saving
        # full_response = []
        
        # # Stream chunks
        # for chunk in stream:
        #     if chunk.choices[0].delta.content:
        #         content = chunk.choices[0].delta.content
        #         full_response.append(content)
        #         yield content


        ## Using Ollama
        stream = self.ollama_client.chat(
            model = self.ollama_model,
            messages=messages,
            stream=True
        )
        
        # Collect full response for saving
        full_response = []
        
        # Stream chunks
        for chunk in stream:
            if chunk.message.content:
                content = chunk.message.content
                full_response.append(content)
                yield content
        
        # Save to chat history after streaming completes
        if self.db_manager:
            answer = "".join(full_response)
            
            # Save user query
            user_entry = ChatHistorySchema(
                message=query,
                role="user",
                file_id=file_id,
                created_at=datetime.now(timezone.utc)
            )
            self.db_manager.insert_data(ChatHistory, user_entry)
            
            # Save assistant response
            assistant_entry = ChatHistorySchema(
                message=answer,
                role="assistant",
                file_id=file_id,
                created_at=datetime.now(timezone.utc)
            )
            self.db_manager.insert_data(ChatHistory, assistant_entry)
    
    def clear_chat_history(self, file_id: str):
        """
        Clear chat history for a specific file_id
        """
        if not self.db_manager:
            return False
        
        try:
            history = self.db_manager.filter_data(ChatHistory, file_id=file_id)
            for chat in history:
                self.db_manager.delete_data(ChatHistory, chat.id)
            return True
        except Exception as e:
            print(f"Error clearing chat history: {e}")
            return False
        