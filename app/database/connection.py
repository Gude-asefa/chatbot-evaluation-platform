
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Locate the project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Load environment variables from the project root
load_dotenv(BASE_DIR / ".env")

# Read the database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured in .env")

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Create database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
