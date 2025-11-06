"""Main FastAPI application for the Summarizer backend."""
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.views.endpoints import router
from contextlib import asynccontextmanager
from app.dependencies import get_embedding_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Summarizer API...")
    
    # Pre-load embedding model at startup
    print("📦 Pre-loading embedding model...")
    embedding_manager = get_embedding_manager()
    _ = embedding_manager.model  # Trigger model loading
    print("✅ Embedding model loaded successfully!")
    
    yield
    
    print("👋 Shutting down Summarizer API...")

app = FastAPI(title="Summarizer API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Summarizer API!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/metrics")
async def get_metrics():
    """Get performance metrics"""
    from app.dependencies import _embedding_manager, _db_manager
    
    return {
        "embedding_manager_loaded": _embedding_manager is not None,
        "db_manager_loaded": _db_manager is not None,
        "model_cached": _embedding_manager._model is not None if _embedding_manager else False
    }