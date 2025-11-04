from fastapi import APIRouter, UploadFile, File, status
from fastapi.responses import JSONResponse
from typing import Optional
from app.ingestion import IngestionManager
from app.embeddings.vectorstore import VectorStore
from app.embeddings import EmbeddingManager
from app.retriever import RetrievalManager
from app.utils import generate_audio_transcript
from app.schema.query_schema import YoutubeSchema
from app.enums import EmbedddingCollectionEnum
from groq import Groq

router = APIRouter()

ingestion_manager = IngestionManager()
embedding_manager = EmbeddingManager()

content_type = ["video/mp4", "audio/mpeg", "audio/wav", "audio/mp3"]


@router.post("/ingest/youtube/{url}")
async def ingest_youtube_video(user_query: YoutubeSchema):
    """Endpoint to ingest a YouTube video by URL"""
    yt_vector_store = VectorStore(embedding_manager=embedding_manager, 
                                  collection_name=EmbedddingCollectionEnum.YOUTUBE_EMBEDDINGS.value
                                  )
    
    yt_retriever = RetrievalManager(vector_store=yt_vector_store)
    
    documents = ingestion_manager.load_youtube_video(user_query.url)
    embeddings = embedding_manager.create_embeddings([doc.page_content for doc in documents])
    yt_vector_store.add_youtube_documents(documents=documents, embeddings=embeddings)

    if user_query.query is None:
        response = yt_retriever.summarize_youtube_video(user_query.url)
    elif user_query.query:
        response = yt_retriever.search_and_summarize(user_query.query)

    return JSONResponse(content=response)


@router.post("/ingest/audio/")
async def ingest_audio_file(
    audio_file: UploadFile = File(...),
    query: Optional[str] = None
):
    """Endpoint to ingest an audio file and process it"""

    audio_vector_store = VectorStore(collection_name=EmbedddingCollectionEnum.AUDIO_EMBEDDINGS.value,
                                     embedding_manager=embedding_manager)
    
    audio_retriever = RetrievalManager(vector_store=audio_vector_store)

    user_query = query
    file = audio_file
    
    if file.content_type not in content_type:
        return JSONResponse(content={"error": "Unsupported file type."},
                            status_code=status.HTTP_400_BAD_REQUEST)
    
    # Load and transcribe audio file
    response = await generate_audio_transcript(file=file)

    chunks = ingestion_manager.split_text(response.text)
    embeddings = embedding_manager.create_embeddings(chunks)
    
    audio_vector_store.add_audio_documents(filename=file.filename,
                                           documents=chunks,
                                           embeddings=embeddings)

    if user_query is None:
        response = audio_retriever.summarize_audio_file(file.filename)    
    else:
        response = audio_retriever.search_and_summarize(user_query)

    return JSONResponse(content=response)
