"""Main FastAPI application for the Summarizer backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.views.endpoints import router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Summarizer API...")
    
    yield

app = FastAPI(title="Summarizer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Define the root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Summarizer API!"}
