import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omnivid.db")

# SQLite 需要 check_same_thread=False 供 FastAPI 多线程使用
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def _migrate_analysis_history():
    """为已有数据库补全新增列（SQLite create_all 不会 ALTER）。"""
    from sqlalchemy import inspect, text

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


def init_db():
    from models import AnalysisHistory, Membership, StripeEvent, UsageDaily, User  # noqa: F401

    db_path = DATABASE_URL.replace("sqlite:///", "")
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
