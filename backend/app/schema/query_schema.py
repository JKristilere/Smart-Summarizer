from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, File
from datetime import datetime, timezone


class YoutubeSchema(BaseModel):
    url: str
    query: Optional[str] = None

class AudioSchema(BaseModel):
    file: UploadFile = File
    query: Optional[str] = None

class ChatHistory(BaseModel):
    file_id: str
    conversation_id: str
    role: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    # user_id: str
    message: str
    conversation_id: str = None

class UserCreate(BaseModel):
    username: str
    password: str
