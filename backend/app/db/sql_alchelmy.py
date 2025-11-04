from sqlalchemy import create_engine
from config import settings
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Type, Dict, List, Optional

DATABASE_URI = settings.DATABASE_URI

engine = create_engine(DATABASE_URI)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
class DBManager:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.session = self.SessionLocal()
        self.Base = declarative_base()
    
    def get_db(self):
        db = self.session
        try:
            yield db
        finally:
            db.close()
    
    def create_tables(self):
        try:
            self.Base.metadata.create_all(bind=self.engine)
            return True
        except Exception as e:
            return f"Failed to create tables: {e}"
    
    def list_tables(self):
        print(self.Base.metadata.tables)
        return self.Base.metadata.tables
        
    def drop_tables(self):
        try:
            self.Base.metadata.drop_all(bind=self.engine)
            return True
        except Exception as e:
            return f"Failed to drop tables: {e}"

    def insert_data(self, model: Type[Any], data: Any):
        try: 
            instance = model(**data.model_dump())
            self.session.add(instance)
            self.session.commit()
            self.session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to insert data: {e}")
    
    def delete_data(self,model: Type[Any], record_id: Any):
        try:
            instance = self.session.query(model).get(record_id)
            if not instance:
                raise ValueError(f"Record with id {record_id} not found.")
            self.session.delete(instance)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to delete data: {e}")
        
    def filter_by_id(self, model: Type[Any], record_id: Any):
        try:
            instance = self.session.query(model).get(record_id)
            if not instance:
                raise ValueError(f"Record with id {record_id} not found.")
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to filter data: {e}")
    
    def filter_data(self, model: Type[Any], **kwargs):
        try:
            return self.session.query(model).filter_by(**kwargs).all()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to filter data: {e}")
        
    def update(self, model: Type[Any], record_id: Any, data: Any):
        """
        Update an existing record by ID.
        """
        try:
            instance = self.session.query(model).get(record_id)
            if not instance:
                raise ValueError(f"{model.__name__} with id {record_id} not found")

            for key, value in data.items():
                setattr(instance, key, value)

            self.session.commit()
            self.session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database update failed: {e}")




# import psycopg2
# from dotenv import load_dotenv
# import os
# from typing import Any

# # Load environment variables from .env (if present)
# load_dotenv()

# # Prefer a single DATABASE_URL if provided (e.g. postgres://user:pass@host:port/dbname)
# DATABASE_URL = os.getenv("DATABASE_URL")

# postgres_user = os.getenv('POSTGRES_USER')
# postgres_password = os.getenv('POSTGRES_PASSWORD')
# postgres_db = os.getenv('POSTGRES_DB')
# postgres_host = os.getenv("POSTGRES_HOST", "localhost")
# postgres_port = os.getenv('POSTGRES_PORT', "5432")



# class DBManager:
#     def __init__(self):
#         self.db_name = postgres_db
#         self.user=postgres_user
#         self.password=postgres_password
#         self.host=postgres_host
#         self.port=postgres_port
#         # If DATABASE_URL is provided, use it. Otherwise build from individual env vars.
#         try:
#             if DATABASE_URL:
#                 self.conn = psycopg2.connect(DATABASE_URL)
#             else:
#                 # Ensure required parameters exist
#                 missing = []
#                 if not self.db_name:
#                     missing.append('POSTGRES_DB')
#                 if not self.user:
#                     missing.append('POSTGRES_USER')
#                 if not self.password:
#                     missing.append('POSTGRES_PASSWORD')

#                 if missing:
#                     raise RuntimeError(
#                         f"Missing required database environment variables: {', '.join(missing)}. "
#                         "Provide a DATABASE_URL or set these variables (e.g. in .env)."
#                     )

#                 self.conn = psycopg2.connect(database=self.db_name,
#                                             user=self.user,
#                                             password=self.password,
#                                             host=self.host,
#                                             port=self.port
#                                             )
#         except Exception:
#             # Re-raise with a clearer message for common auth failures
#             raise
#         self.cursor = self.conn.cursor()

#     def __close_connection(self):
#         self.cursor.close()
#         self.conn.close()

#     def create_database(self):
#         try: 
#             self.cursor.execute(
#             f"""
#         CREATE DATABASE IF NOT EXISTS {self.db_name}
#         WITH OWNER = {self.user};
#             """)
#             self.conn.commit()
#             self.__close_connection()
#             return True

#         except Exception as e:
#             print(e)
#             return False
    
#     def create_table(self, table_name:str, schema: Any):
#         try:
#             self.cursor.execute(f"""
#                             CREATE TABLE IF NOT EXISTS {table_name} (
#                             {schema})
#                             """)
#             self.conn.commit()
#             self.__close_connection()
#             return True
#         except Exception as e:
#             print(e)
#             return False
    
#     def insert_data(self, table_name: str, columns: str, values: tuple):
#         try:
#             placeholders = ', '.join(['%s'] * len(values))
#             self.cursor.execute(f"""
#                                 INSERT INTO {table_name} ({columns})
#                                 VALUES ({placeholders})
#                                 """, values)
#             self.conn.commit()
#             self.__close_connection()
#             return True
#         except Exception as e:
#             print(e)
#             return False

#     def query_data(self, table_name: str, condition: str = None):
#         try :
#             if condition:
#                 self.cursor.execute(
#                     f"""
#                     SELECT * FROM {table_name}
#                     WHERE {condition}
#                     """
#                 )
#             else:
#                 self.cursor.execute(
#                     f"""
#                     SELECT * FROM {table_name}
#                     """
#                 )
#             results = self.cursor.fetchall()
#             self.__close_connection()
#             return results
#         except Exception as e:
#             print(e)
#             return False
    
#     def update_data(self, table_name: str, updates: str, condition: str):
#         try:
#             self.cursor.execute(
#             f"""
#             UPDATE {table_name}
#             SET {updates}
#             WHERE {condition}
#             """
#             )
#             self.conn.commit()
#             self.__close_connection()
#             return True
#         except Exception as e:
#             return e
    
#     def delete_data(self, table_name: str, condition: str):
#         try: 
#             self.cursor.execute(
#                 f"""
#                 DELETE FROM {table_name}
#                 WHERE {condition}
#                 """
#             )
#             self.conn.commit()
#             self.__close_connection()
#             return True
    
#         except Exception as e:
#             print(e)
#             return False
    
#     def delete_table(self, table_name: str):
#         try:
#             self.cursor.execute(
#             f"""
#             DROP TABLE IF EXISTS {table_name}
#             """
#             )
#             self.conn.commit()
#             self.__close_connection()

#             return True
#         except Exception as e:
#             print(e)
#             return False
    
#     def list_tables(self):
#         self.cursor.execute(
#             f"""
#             SELECT table_name
#             FROM information_schema.tables
#             where table_type = 'BASE TABLE' AND table_schema='public'
#             ORDER BY table_name
#             """
#         )

#         tables = self.cursor.fetchall()
#         self.__close_connection()
#         return tables
    
    
#     def delete_tables(self):
#         tables = self.list_tables()
#         for table in tables:
#             self.delete_table(table_name=table[0])
#         self.__close_connection()
#         return True
    
    

        
    
