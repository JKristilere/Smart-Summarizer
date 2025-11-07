from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, File
from datetime import datetime, timezone



class YoutubeSchema(BaseModel):
    url: str
    query: Optional[str] = None

class YoutubeStoreSchema(BaseModel):
    url: str
    video_id :str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AudioStoreSchema(BaseModel):
    file_id: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AudioSchema(BaseModel):
    file: UploadFile = File
    query: Optional[str] = None

class ChatHistorySchema(BaseModel):
    """Schema for storing chat messages"""
    role: str  # "user" or "assistant"
    message: str
    file_id: Optional[str] = None  # video_id or audio file_id to link chat to content
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    """Schema for chat requests"""
    query: str
    file_id: str  # video_id or audio file_id
    include_vector_search: bool = True
    top_k: int = 3


class ChatHistoryRequest(BaseModel):
    """Schema for retrieving chat history"""
    file_id: str
    limit: int = 50