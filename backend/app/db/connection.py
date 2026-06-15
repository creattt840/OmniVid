from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()

connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _migrate_analysis_history() -> None:
    """为已有数据库补全新增列（SQLite create_all 不会 ALTER）。"""
    inspector = inspect(engine)
    if "analysis_history" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("analysis_history")}
    additions = [
        ("segments_json", "TEXT NOT NULL DEFAULT '[]'"),
        ("article_content", "TEXT NOT NULL DEFAULT ''"),
        ("chat_history_json", "TEXT NOT NULL DEFAULT '[]'"),
        ("transcript_source", "VARCHAR(16) NOT NULL DEFAULT ''"),
    ]
    with engine.begin() as conn:
        for name, col_def in additions:
            if name not in existing:
                conn.execute(text(f"ALTER TABLE analysis_history ADD COLUMN {name} {col_def}"))


def init_db() -> None:
    from app.db import models  # noqa: F401

    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path and db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _migrate_analysis_history()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
