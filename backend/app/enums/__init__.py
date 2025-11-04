from enum import Enum


class TablenameEnum(str, Enum):
    YOUTUBE = "youtube"
    AUDIO = "audio"
    PODCAST = "podcast"
    CONVERSATIONS = "conversations"
    USERS = "users"

class EmbedddingCollectionEnum(str, Enum):
    YOUTUBE_EMBEDDINGS = "youtube_embeddings"
    AUDIO_EMBEDDINGS = "audio_embeddings"
    PODCAST_EMBEDDINGS = "podcast_embeddings"
    CONVERSATIONS_EMBEDDINGS = "conversations_embeddings"