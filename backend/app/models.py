# backend/app/models.py
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app import settings

def db_url() -> str:
    return (
        f"postgresql+psycopg://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )

_engine: Optional[Engine] = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(db_url(), pool_pre_ping=True)
    return _engine

def init_db():
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kb_docs (
                id SERIAL PRIMARY KEY,
                title TEXT,
                body TEXT,
                source TEXT,
                embedding vector(1536)
            )
        """))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS kb_docs_idx ON kb_docs USING ivfflat (embedding vector_cosine_ops)")
        )

