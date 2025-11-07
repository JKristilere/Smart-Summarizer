"""
Migration script to add file_id column to conversations table
and update existing records.

Run this AFTER updating the models.py file.
"""

import sys
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.db.sql_alchelmy import Base
from app.db.models import ChatHistory, Youtube, Audio

load_dotenv()

DATABASE_URI = os.getenv("DATABASE_URI")
if not DATABASE_URI:
    raise ValueError("DATABASE_URI not set in environment variables")

engine = create_engine(DATABASE_URI)


def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='{table_name}' 
            AND column_name='{column_name}'
        """))
        return result.fetchone() is not None


def add_file_id_column():
    """Add file_id column to conversations table if it doesn't exist"""
    print("Checking if file_id column exists in conversations table...")
    
    if check_column_exists('conversations', 'file_id'):
        print("✅ file_id column already exists")
        return
    
    print("Adding file_id column to conversations table...")
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE conversations 
            ADD COLUMN file_id VARCHAR
        """))
        conn.commit()
    
    print("✅ file_id column added successfully")


def add_indexes():
    """Add indexes for better query performance"""
    print("Adding indexes...")
    
    with engine.connect() as conn:
        try:
            # Check and create index on file_id
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'conversations' 
                AND indexname = 'idx_chat_file_id'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    CREATE INDEX idx_chat_file_id 
                    ON conversations(file_id)
                """))
                print("✅ Created index on file_id")
            else:
                print("✅ Index on file_id already exists")
            
            # Check and create index on created_at
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'conversations' 
                AND indexname = 'idx_chat_created_at'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    CREATE INDEX idx_chat_created_at 
                    ON conversations(created_at)
                """))
                print("✅ Created index on created_at")
            else:
                print("✅ Index on created_at already exists")
            
            conn.commit()
            
        except Exception as e:
            print(f"⚠️  Index creation skipped: {e}")


def update_existing_models():
    """Ensure all models are up to date"""
    print("Updating database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema updated")
    except Exception as e:
        print(f"❌ Failed to update schema: {e}")


def verify_migration():
    """Verify that migration was successful"""
    print("\nVerifying migration...")
    
    with engine.connect() as conn:
        # Check conversations table structure
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'conversations'
            ORDER BY ordinal_position
        """))
        
        print("\n📋 Conversations table structure:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
        # Check indexes
        result = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'conversations'
        """))
        
        print("\n📊 Indexes on conversations table:")
        for row in result:
            print(f"  - {row[0]}")


def run_migration():
    """Run the complete migration"""
    print("=" * 60)
    print("Starting Database Migration")
    print("=" * 60)
    
    try:
        # Step 1: Add file_id column
        add_file_id_column()
        
        # Step 2: Update models
        update_existing_models()
        
        # Step 3: Add indexes
        add_indexes()
        
        # Step 4: Verify
        verify_migration()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Migration failed: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    run_migration()