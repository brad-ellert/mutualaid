from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URI, pool_pre_ping=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

def get_db():
    ""
    Dependency function that yields database sessions.
    
    This function is used by FastAPI's dependency injection system to provide
    a database session to each request. The session is automatically closed
    when the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
