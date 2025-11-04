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
    # user_id: str
    role: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))