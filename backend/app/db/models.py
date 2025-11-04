from app.db.sql_alchelmy import Base
from sqlalchemy import Column, Integer, String, DateTime, VARCHAR
from app.enums import TablenameEnum

class ChatHistory(Base):
    __tablename__ = TablenameEnum.CONVERSATIONS.value
    id = Column(Integer, primary_key=True, 
                index=True, autoincrement=True)
    # user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    message = Column(String(100000000000000000), nullable=False)
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"""
                ChatHistory(id={self.id}, 
                # user_id={self.user_id}, 
                conversation_id={self.conversation_id}, 
                role={self.role}, 
                message={self.message}, 
                created_at={self.created_at})
                """

class Youtube(Base):
    __tablename__ = TablenameEnum.YOUTUBE.value
    id = Column(Integer, primary_key=True, 
                index=True, autoincrement=True)
    video_id = Column(String, nullable=False)
    content = Column(String(100000000000000000), nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"""
                Youtube(id={self.id}, 
                video_id={self.video_id}, 
                content={self.content}, 
                url={self.url}, 
                created_at={self.created_at})
                """
    

class Audio(Base):
    __tablename__ = TablenameEnum.AUDIO.value
    id = Column(Integer, primary_key=True, 
                autoincrement=True, index=True)
    file_id = Column(String(100000000000000000), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"""Audio(id={self.id}, 
                file_id={self.file_id}, 
                content={self.content}, 
                created_at={self.created_at})
                """