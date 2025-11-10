"""
Shared FastAPI dependencies.
"""
from typing import Generator

from sqlalchemy.orm import Session

from src.config.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
