from fastapi import APIRouter, UploadFile, File, status, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Annotated
from app.ingestion import IngestionManager
from app.embeddings.vectorstore import VectorStore
from app.embeddings import EmbeddingManager
from app.retriever import RetrievalManager
from app.utils import generate_audio_transcript, extract_video_id
from app.schema import (YoutubeSchema, ChatRequest, ChatHistoryRequest)
from app.enums import EmbedddingCollectionEnum
from app.dependencies import get_embedding_manager, get_ingestion_manager, get_db_manager
from app.db import DBManager

router = APIRouter()

content_type = ["video/mp4", "audio/mpeg", "audio/wav", "audio/mp3", "audio/x-m4a"]


@router.post("/ingest/youtube/")
async def ingest_youtube_video(
    user_query: YoutubeSchema,
    ingestion_manager: Annotated[IngestionManager, Depends(get_ingestion_manager)],
    embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)],
    db_manager: Annotated[DBManager, Depends(get_db_manager)]
):
    """Endpoint to ingest a YouTube video by URL"""
    try:
        # Create vector store with db_manager
        yt_vector_store = VectorStore(
            embedding_manager=embedding_manager,
            db_manager=db_manager,
            collection_name=EmbedddingCollectionEnum.YOUTUBE_EMBEDDINGS.value
        )
        
        yt_retriever = RetrievalManager(
            vector_store=yt_vector_store,
            db_manager=db_manager
        )
        
        # Load documents
        documents = ingestion_manager.load_youtube_video(user_query.url)
        
        # Batch embeddings for efficiency
        embeddings = embedding_manager.create_embeddings(
            [doc.page_content for doc in documents]
        )
        
        video_id = yt_vector_store.add_youtube_documents(
            documents=documents, 
            embeddings=embeddings
        )
        
        # video_id = extract_video_id(user_query.url)

        if user_query.query is None:
            response = yt_retriever.summarize_youtube_video(user_query.url)
        else:
            response = yt_retriever.search_and_summarize(
                user_query.query,
                file_id=video_id
            )

        return JSONResponse(content={
            "summary": response,
            "video_id": video_id,
            "status": "success"
        },
        status_code=status.HTTP_201_CREATED)
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "status": "failed"}, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/ingest/audio/")
async def ingest_audio_file(
    ingestion_manager: Annotated[IngestionManager, Depends(get_ingestion_manager)],
    embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)],
    db_manager: Annotated[DBManager, Depends(get_db_manager)],
    audio_file: UploadFile = File(...),
    query: Optional[str] = None,
):
    """Endpoint to ingest an audio file and process it"""
    try:
        if audio_file.content_type not in content_type:
            return JSONResponse(
                content={"error": f"Unsupported file type: {audio_file.content_type}", "status": "failed"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        audio_vector_store = VectorStore(
            collection_name=EmbedddingCollectionEnum.AUDIO_EMBEDDINGS.value,
            embedding_manager=embedding_manager,
            db_manager=db_manager
        )
        
        audio_retriever = RetrievalManager(
            vector_store=audio_vector_store,
            db_manager=db_manager
        )
        
        # Transcribe audio
        response = await generate_audio_transcript(file=audio_file)
        
        # Split and embed
        chunks = ingestion_manager.split_text(response.text)
        embeddings = embedding_manager.create_embeddings(chunks)
        
        file_id = audio_vector_store.add_audio_documents(
            filename=audio_file.filename,
            documents=chunks,
            embeddings=embeddings
        )
        
        if query is None:
            result = audio_retriever.summarize_audio_file(file_id)    
        else:
            result = audio_retriever.search_and_summarize(
                query,
                file_id=file_id
            )

        return JSONResponse(content={
            "summary": result,
            "file_id": file_id,
            "status": "success"
        })
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "status": "failed"}, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/chat/")
async def chat_with_content(
    chat_request: ChatRequest,
    embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)],
    db_manager: Annotated[DBManager, Depends(get_db_manager)]
):
    """
    Chat with the content (YouTube video or audio file) using chat history.
    
    The file_id should be:
    - video_id for YouTube videos (extracted from URL)
    - file_id for audio files (returned from /ingest/audio/)
    """
    try:
        # Determine collection based on file_id pattern
        # YouTube video IDs are typically 11 characters
        if len(chat_request.file_id) == 11:
            collection_name = EmbedddingCollectionEnum.YOUTUBE_EMBEDDINGS.value
        else:
            collection_name = EmbedddingCollectionEnum.AUDIO_EMBEDDINGS.value
        
        vector_store = VectorStore(
            collection_name=collection_name,
            embedding_manager=embedding_manager,
            db_manager=db_manager
        )
        
        retriever = RetrievalManager(
            vector_store=vector_store,
            db_manager=db_manager
        )
        
        response = retriever.chat_with_context(
            query=chat_request.query,
            file_id=chat_request.file_id,
            include_vector_search=chat_request.include_vector_search,
            top_k=chat_request.top_k
        )
        
        return JSONResponse(content={
            "response": response,
            "file_id": chat_request.file_id,
            "status": "success"
        })
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "status": "failed"}, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/chat/stream/")
async def chat_with_content_streaming(
    chat_request: ChatRequest,
    embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)],
    db_manager: Annotated[DBManager, Depends(get_db_manager)]
):
    """
    Stream chat responses with the content (YouTube video or audio file).
    """
    try:
        # Determine collection based on file_id pattern
        if len(chat_request.file_id) == 11:
            collection_name = EmbedddingCollectionEnum.YOUTUBE_EMBEDDINGS.value
        else:
            collection_name = EmbedddingCollectionEnum.AUDIO_EMBEDDINGS.value
        
        vector_store = VectorStore(
            collection_name=collection_name,
            embedding_manager=embedding_manager,
            db_manager=db_manager
        )
        
        retriever = RetrievalManager(
            vector_store=vector_store,
            db_manager=db_manager
        )
        
        async def generate():
            async for chunk in retriever.chat_with_context_streaming(
                query=chat_request.query,
                file_id=chat_request.file_id,
                include_vector_search=chat_request.include_vector_search,
                top_k=chat_request.top_k
            ):
                yield chunk
        
        return StreamingResponse(
            generate(),
            media_type="text/plain"
        )
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "status": "failed"}, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/chat/history/")
async def get_chat_history(
    history_request: ChatHistoryRequest,
    embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)],
    db_manager: Annotated[DBManager, Depends(get_db_manager)]
):
    """
    Retrieve chat history for a specific file_id (video_id or audio file_id).
    """
    try:
        # Determine collection based on file_id pattern
        if len(history_request.file_id) == 11:
            collection_name = EmbedddingCollectionEnum.YOUTUBE_EMBEDDINGS.value
        else:
            collection_name = EmbedddingCollectionEnum.AUDIO_EMBEDDINGS.value
        
        vector_store = VectorStore(
            collection_name=collection_name,
            embedding_manager=embedding_manager,
            db_manager=db_manager
        )
        
        retriever = RetrievalManager(
            vector_store=vector_store,
            db_manager=db_manager
        )
        
        history = retriever.get_chat_history(
            file_id=history_request.file_id,
            limit=history_request.limit
        )
        
        # Convert to dict for JSON response
        history_data = [
            {
                "id": chat.id,
                "role": chat.role,
                "message": chat.message,
                "file_id": chat.file_id,
                "created_at": chat.created_at.isoformat()
            }
            for chat in history
        ]
        
        return JSONResponse(content={
            "history": history_data,
            "count": len(history_data),
            "status": "success"
        })
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "status": "failed"}, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/chat/history/{file_id}")
async def clear_chat_history(
    file_id: str,
    embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)],
    db_manager: Annotated[DBManager, Depends(get_db_manager)]
):
    """
    Clear chat history for a specific file_id.
    """
    try:
        # Determine collection based on file_id pattern
        if len(file_id) == 11:
            collection_name = EmbedddingCollectionEnum.YOUTUBE_EMBEDDINGS.value
        else:
            collection_name = EmbedddingCollectionEnum.AUDIO_EMBEDDINGS.value
        
        vector_store = VectorStore(
            collection_name=collection_name,
            embedding_manager=embedding_manager,
            db_manager=db_manager
        )
        
        retriever = RetrievalManager(
            vector_store=vector_store,
            db_manager=db_manager
        )
        
        success = retriever.clear_chat_history(file_id)
        
        if success:
            return JSONResponse(content={
                "message": f"Chat history cleared for {file_id}",
                "status": "success"
            })
        else:
            return JSONResponse(
                content={"error": "Failed to clear chat history", "status": "failed"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "status": "failed"}, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )