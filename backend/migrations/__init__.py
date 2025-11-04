import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker



class DBSetup:
    def __init__(self, db_url, Base):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()
        self.Base = Base
    
    def create_tables(self):
        try:
            self.tables = self.Base.metadata.create_all(bind=self.engine)
            print(f"Created tables: {self.tables}")
        except Exception as e:
            return f"Failed to create tables: {e}"

    def drop_tables(self):
        try:
            self.tables = self.Base.metadata.drop_all(bind=self.engine)
            print(f"Dropped tables: {self.tables}")
        except Exception as e:
            return f"Failed to drop tables: {e}"