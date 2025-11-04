"""Script for ingesting documents from youtube url, podcast rss feed, or audio files"""
from typing import Optional
from langchain_community.document_loaders.youtube import YoutubeLoader, TranscriptFormat
from langchain_text_splitters import RecursiveCharacterTextSplitter
from groq import Groq


class IngestionManager:
    """class to manage ingestion of documents from various sources"""

    def load_youtube_video(self, url: str):
        """Load a youtube video from a url"""
        loader = YoutubeLoader.from_youtube_url(
            youtube_url=url,
            transcript_format=TranscriptFormat.CHUNKS,
            # add_video_info=True,
            chunk_size_seconds=30
        )

        if not loader:
            raise ValueError(f"Could not load YouTube video from URL: {url}. Please check the URL and try again.")

        # documents = [doc.page_content for doc in loader.load()]
        documents = loader.load()

        return documents

    def load_audio_file(self, file_path: str, source_language: Optional[str] = None) -> str:
        """
        Load and transcribe an audio file using Groq's Whisper model.
        
        Args:
            file_path (str): Path to the audio

        Returns:
            str: Transcribed text from the audio file
        """
        client = Groq()
        response = client.audio.transcriptions.create(
            file=open(file_path, "rb"),
            model="whisper-large-v3",
            language=source_language
        )
        
        return response.text
    
    def split_text(self,text: str, chunk_size: int = 1000, chunk_overlap: int = 20):
        """
        Split text into smaller chunks using RecursiveCharacterTextSplitter.
        
        Args:
            text (str): The text to split
            chunk_size (int): The maximum size of each chunk
            chunk_overlap (int): The number of overlapping characters between chunks
        
        Returns:
            List[str]: A list of text chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        
        return text_splitter.split_text(text)
    
