import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
