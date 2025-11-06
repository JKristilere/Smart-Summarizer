from sqlalchemy import create_engine, pool
from config import settings
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Type, Dict, List, Optional
from functools import lru_cache


_engine = None

def get_engine(db_url: str):
    global _engine
    if _engine is None:
        _engine = create_engine(
            db_url,
            poolclass=pool.QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600   # Recycle connections after 1 hour
        )
    return _engine

Base = declarative_base()

class DBManager:
    def __init__(self, db_url):
        self.engine = get_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.Base = Base  # Use the global Base
    
    def _get_session_context(self):
        """Internal method to get a session for operations"""
        return self.SessionLocal()
    
    def get_session(self):
        """Context manager for sessions (for use with 'with' statement)"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
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
        session = self._get_session_context()
        try: 
            instance = model(**data.model_dump())
            session.add(instance)
            session.commit()
            session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Failed to insert data: {e}")
        finally:
            session.close()
    
    def delete_data(self, model: Type[Any], record_id: Any):
        session = self._get_session_context()
        try:
            instance = session.query(model).get(record_id)
            if not instance:
                raise ValueError(f"Record with id {record_id} not found.")
            session.delete(instance)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Failed to delete data: {e}")
        finally:
            session.close()
        
    def filter_by_id(self, model: Type[Any], record_id: Any):
        session = self._get_session_context()
        try:
            instance = session.query(model).get(record_id)
            if not instance:
                raise ValueError(f"Record with id {record_id} not found.")
            return instance
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Failed to filter data: {e}")
        finally:
            session.close()
    
    def filter_data(self, model: Type[Any], **kwargs):
        session = self._get_session_context()
        try:
            return session.query(model).filter_by(**kwargs).all()
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Failed to filter data: {e}")
        finally:
            session.close()
        
    def update(self, model: Type[Any], record_id: Any, data: Any):
        """
        Update an existing record by ID.
        """
        session = self._get_session_context()
        try:
            instance = session.query(model).get(record_id)
            if not instance:
                raise ValueError(f"{model.__name__} with id {record_id} not found")

            for key, value in data.items():
                setattr(instance, key, value)

            session.commit()
            session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Database update failed: {e}")
        finally:
            session.close()



# from sqlalchemy import create_engine, pool
# from config import settings
# from sqlalchemy.orm import declarative_base, sessionmaker
# from sqlalchemy.exc import SQLAlchemyError
# from typing import Any, Type, Dict, List, Optional
# from functools import lru_cache


# _engine = None

# def get_engine(db_url:str):
#     global _engine
#     if _engine is None:
#         _engine = create_engine(
#             db_url,
#             poolclass=pool.QueuePool,
#             pool_size=5,
#             max_overflow=10,
#             pool_pre_ping=True,  # Verify connections before using
#             pool_recycle=3600   # Recycle connections after 1 hour
#         )
#     return _engine

# Base = declarative_base()

# class DBManager:
#     def __init__(self, db_url):
#         self.engine = get_engine(db_url)
#         self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
#         # self.session = self.SessionLocal()
#         self.Base = declarative_base()
    
#     def get_session(self):
#         self.session = self.SessionLocal()
#         try:
#             yield self.session
#             self.session.commit()
#         except Exception:
#             self.session.rollback()
#             raise
#         finally:
#             self.session.close()
    
#     # def get_db(self):
#     #     db = self.session
#     #     try:
#     #         yield db
#     #     finally:
#     #         db.close()
    
#     def create_tables(self):
#         try:
#             self.Base.metadata.create_all(bind=self.engine)
#             return True
#         except Exception as e:
#             return f"Failed to create tables: {e}"
    
#     def list_tables(self):
#         print(self.Base.metadata.tables)
#         return self.Base.metadata.tables
        
#     def drop_tables(self):
#         try:
#             self.Base.metadata.drop_all(bind=self.engine)
#             return True
#         except Exception as e:
#             return f"Failed to drop tables: {e}"

#     def insert_data(self, model: Type[Any], data: Any):
#         try: 
#             instance = model(**data.model_dump())
#             self.session.add(instance)
#             self.session.commit()
#             self.session.refresh(instance)
#             return instance
#         except SQLAlchemyError as e:
#             self.session.rollback()
#             raise RuntimeError(f"Failed to insert data: {e}")
    
#     def delete_data(self,model: Type[Any], record_id: Any):
#         try:
#             instance = self.session.query(model).get(record_id)
#             if not instance:
#                 raise ValueError(f"Record with id {record_id} not found.")
#             self.session.delete(instance)
#             self.session.commit()
#             return True
#         except SQLAlchemyError as e:
#             self.session.rollback()
#             raise RuntimeError(f"Failed to delete data: {e}")
        
#     def filter_by_id(self, model: Type[Any], record_id: Any):
#         try:
#             instance = self.session.query(model).get(record_id)
#             if not instance:
#                 raise ValueError(f"Record with id {record_id} not found.")
#             return instance
#         except SQLAlchemyError as e:
#             self.session.rollback()
#             raise RuntimeError(f"Failed to filter data: {e}")
    
#     def filter_data(self, model: Type[Any], **kwargs):
#         try:
#             return self.session.query(model).filter_by(**kwargs).all()
#         except SQLAlchemyError as e:
#             self.session.rollback()
#             raise RuntimeError(f"Failed to filter data: {e}")
        
#     def update(self, model: Type[Any], record_id: Any, data: Any):
#         """
#         Update an existing record by ID.
#         """
#         try:
#             instance = self.session.query(model).get(record_id)
#             if not instance:
#                 raise ValueError(f"{model.__name__} with id {record_id} not found")

#             for key, value in data.items():
#                 setattr(instance, key, value)

#             self.session.commit()
#             self.session.refresh(instance)
#             return instance
#         except SQLAlchemyError as e:
#             self.session.rollback()
#             raise RuntimeError(f"Database update failed: {e}")
    
