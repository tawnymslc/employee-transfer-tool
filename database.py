import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

if not os.getenv("DATABASE_URL"):
    load_dotenv(".env.development")

# Get database connection credentials from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Configures SQLAlchemy to communicate with PostgreSQL
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()