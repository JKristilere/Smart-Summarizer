import sys

from dotenv import load_dotenv
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine
from app.db.sql_alchelmy import Base
from app.db.models import ChatHistory, Youtube, Audio  # Import your models

load_dotenv()

DATABASE_URI = os.getenv("DATABASE_URI")
if not DATABASE_URI:
    raise ValueError("DATABASE_URI not set in environment variables")

engine = create_engine(DATABASE_URI)

def init_db():
    """Initialize database by creating all tables from models."""
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
def drop_db():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables dropped successfully!")

if __name__ == "__main__":
    init_db()
    # drop_db()
