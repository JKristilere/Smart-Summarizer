from urllib.parse import urlparse, parse_qs
import asyncio
from fastapi import UploadFile
import os
from groq import Groq
from config import settings

groq_api_key = settings.GROQ_API_KEY
client = Groq(api_key=groq_api_key)
content_type = ["video/mp4", "audio/mpeg", "audio/wav", "audio/mp3"]


def extract_video_id(url: str) -> str:
    """Extracts YouTube video ID from a URL like https://youtube.com/watch?v=jkotu123"""
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    return query.get("v", [None])[0]

async def generate_audio_transcript(file: UploadFile):
      data = await file.read()
      response = client.audio.transcriptions.create(
        file=(file.filename, data),
        model="whisper-large-v3",
        response_format="verbose_json"
    )
      return response

