"""
Database configuration and session management for the Pharmacy Agent system.
Uses SQLite for local/free-tier and PostgreSQL for production.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL
# Render provides DATABASE_URL starting with "postgres://" but SQLAlchemy
# requires "postgresql://" — fix it automatically.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pharma_agent.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Engine connect_args — only needed for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Ensures proper cleanup after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
