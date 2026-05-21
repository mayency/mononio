import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

# Get database URL from environment or use default
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://marketing_user:secure_password@localhost:5432/marketing_intelligence"
)

# Create engine with connection pooling for production
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False
)


# Updated SQLAlchemy 2.0+ pattern
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db() -> Session:
    """
    Dependency to get database session.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
