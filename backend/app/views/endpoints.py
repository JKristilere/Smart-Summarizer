from fastapi import APIRouter, UploadFile, File, status, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Annotated
from app.ingestion import IngestionManager
from app.db import DBManager
from app.embeddings.vectorstore import VectorStore
from app.embeddings import EmbeddingManager
from app.dependencies import get_ingestion_manager, get_embedding_manager, get_db_manager
from app.retriever import RetrievalManager
from app.utils import generate_audio_transcript
from app.schema.query_schema import YoutubeSchema
from app.enums import EmbedddingCollectionEnum
from groq import Groq

router = APIRouter()


content_type = ["video/mp4", "audio/mpeg", "audio/wav", "audio/mp3"]


@router.post("/ingest/youtube/{url}")
async def ingest_youtube_video(user_query: YoutubeSchema,
                               ingestion_manager: Annotated[IngestionManager, Depends(get_ingestion_manager)],
                               db_manager: Annotated[DBManager, Depends(get_db_manager)],
                               embedding_manager: Annotated[EmbeddingManager, Depends(get_embedding_manager)],
                               ):
    """Endpoint to ingest a YouTube video by URL"""
    try:
        yt_vector_store = VectorStore(embedding_manager=embedding_manager, 
                                    collection_name=EmbedddingCollectionEnum.YOUTUBE_EMBEDDINGS.value,
                                    db_manager=db_manager
                                    )
        
        yt_retriever = RetrievalManager(vector_store=yt_vector_store)
        
        # Load documents
        documents = ingestion_manager.load_youtube_video(user_query.url)

        # Batch embeddings for efficiency
        embeddings = embedding_manager.create_embeddings(
            [doc.page_content for doc in documents]
            )
        
        yt_vector_store.add_youtube_documents(documents=documents, embeddings=embeddings)

        if user_query.query is None:
            response = yt_retriever.summarize_youtube_video(user_query.url)
        elif user_query.query:
            response = yt_retriever.search_and_summarize(user_query.query)

        return JSONResponse(content={"summary": response})
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
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
                content={"error": "Unsupported file type."},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        audio_vector_store = VectorStore(
            collection_name=EmbedddingCollectionEnum.AUDIO_EMBEDDINGS.value,
            embedding_manager=embedding_manager,
            db_manager=db_manager
        )
        
        audio_retriever = RetrievalManager(vector_store=audio_vector_store)
        
        # Transcribe audio
        response = await generate_audio_transcript(file=audio_file)
        
        # Split and embed
        chunks = ingestion_manager.split_text(response.text)
        embeddings = embedding_manager.create_embeddings(chunks)
        
        file_id =audio_vector_store.add_audio_documents(
            filename=audio_file.filename,
            documents=chunks,
            embeddings=embeddings
        )

        if query is None:
            result = audio_retriever.summarize_audio_file(file_id)    
        else:
            result = audio_retriever.search_and_summarize(query)

        return JSONResponse(content={"summary": result})
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )