from app.db.sql_alchelmy import Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.enums import TablenameEnum

class ChatHistory(Base):
    __tablename__ = TablenameEnum.CONVERSATIONS.value
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    message = Column(Text, nullable=False)  # Use Text for large messages
    file_id = Column(String, nullable=True)  # video_id or audio file_id
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"""ChatHistory(id={self.id}, role={self.role}, file_id={self.file_id}, created_at={self.created_at})"""


class Youtube(Base):
    __tablename__ = TablenameEnum.YOUTUBE.value
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(String, nullable=False, unique=True, index=True)  # Add unique constraint
    content = Column(Text, nullable=False)  # Use Text for large content
    url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"""Youtube(id={self.id}, video_id={self.video_id}, url={self.url}, created_at={self.created_at})"""


class Audio(Base):
    __tablename__ = TablenameEnum.AUDIO.value
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    file_id = Column(String, nullable=False, unique=True, index=True)  # Add unique constraint
    content = Column(Text, nullable=False)  # Use Text for large content
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"""Audio(id={self.id}, file_id={self.file_id}, created_at={self.created_at})"""