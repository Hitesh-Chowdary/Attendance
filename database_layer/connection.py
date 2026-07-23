import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables from parent folders or current folder
load_dotenv()

# The user will supply DATABASE_URL in their environment/dotenv file.
# Default to a local PostgreSQL database named 'hardwareattendance'
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./hardwareattendance.db"
)

# Render PostgreSQL URLs start with postgres://, which SQLAlchemy 1.4+ requires as postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connect to database (supports SQLite fallback and PostgreSQL)
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for retrieving database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
