"""分析历史业务逻辑。"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models import AnalysisHistory, User

MAX_HISTORY_PER_USER = 10


def _serialize(record: AnalysisHistory) -> dict:
    analyzed_at = record.analyzed_at
    if analyzed_at.tzinfo is None:
        analyzed_at = analyzed_at.replace(tzinfo=timezone.utc)
    return {
        "id": record.id,
        "url": record.url,
        "source": record.source,
        "title": record.title,
        "platform": record.platform,
        "thumbnail": record.thumbnail,
        "summary": record.summary_json,
        "mindmap": record.mindmap,
        "segments": record.segments_json or [],
        "article": record.article_content or "",
        "chatHistory": record.chat_history_json or [],
        "transcriptSource": record.transcript_source or "",
        "analyzedAt": int(analyzed_at.timestamp() * 1000),
    }


def get_history_record(db: Session, user_id: int, history_id: int) -> AnalysisHistory | None:
    return (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.id == history_id, AnalysisHistory.user_id == user_id)
        .first()
    )


def list_history(db: Session, user_id: int) -> list[dict]:
    records = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == user_id)
        .order_by(AnalysisHistory.analyzed_at.desc())
        .limit(MAX_HISTORY_PER_USER)
        .all()
    )
    return [_serialize(r) for r in records]


def _trim_history(db: Session, user_id: int) -> None:
    records = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == user_id)
        .order_by(AnalysisHistory.analyzed_at.desc())
        .offset(MAX_HISTORY_PER_USER)
        .all()
    )
    for record in records:
        db.delete(record)


def _apply_payload(record: AnalysisHistory, payload: dict) -> None:
    if payload.get("title") is not None:
        record.title = payload.get("title") or ""
    if payload.get("platform") is not None:
        record.platform = payload.get("platform") or ""
    if payload.get("thumbnail") is not None:
        record.thumbnail = payload.get("thumbnail")
    if payload.get("summary") is not None:
        record.summary_json = payload.get("summary") or {}
    if payload.get("mindmap") is not None:
        record.mindmap = payload.get("mindmap") or ""
    if payload.get("segments") is not None:
        record.segments_json = payload.get("segments") or []
    if payload.get("article") is not None:
        record.article_content = payload.get("article") or ""
    if payload.get("chatHistory") is not None:
        record.chat_history_json = payload.get("chatHistory") or []
    if payload.get("transcriptSource") is not None:
        record.transcript_source = payload.get("transcriptSource") or ""


def save_history(db: Session, user: User, payload: dict) -> dict:
    url = payload["url"].strip()
    source = payload.get("source", "url")
    if source not in ("url", "local"):
        source = "local" if url.startswith("local://") else "url"

    existing = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == user.id, AnalysisHistory.url == url)
        .first()
    )
    now = datetime.now(timezone.utc)
    is_partial = payload.get("partial", False)

    if existing:
        if payload.get("source"):
            existing.source = source
        _apply_payload(existing, payload)
        if not is_partial:
            existing.analyzed_at = now
        record = existing
    else:
        record = AnalysisHistory(
            user_id=user.id,
            url=url,
            source=source,
            title=payload.get("title") or "",
            platform=payload.get("platform") or "",
            thumbnail=payload.get("thumbnail"),
            summary_json=payload.get("summary") or {},
            mindmap=payload.get("mindmap") or "",
            segments_json=payload.get("segments") or [],
            article_content=payload.get("article") or "",
            chat_history_json=payload.get("chatHistory") or [],
            transcript_source=payload.get("transcriptSource") or "",
            analyzed_at=now,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    if not is_partial:
        _trim_history(db, user.id)
        db.commit()
    return _serialize(record)


def update_chat_history(db: Session, user_id: int, history_id: int, chat_history: list) -> bool:
    record = get_history_record(db, user_id, history_id)
    if not record:
        return False
    record.chat_history_json = chat_history
    db.commit()
    return True


def update_article_content(db: Session, user_id: int, history_id: int, article: str) -> bool:
    record = get_history_record(db, user_id, history_id)
    if not record:
        return False
    record.article_content = article
    db.commit()
    return True


def delete_history(db: Session, user_id: int, history_id: int) -> bool:
    record = get_history_record(db, user_id, history_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def clear_history(db: Session, user_id: int) -> int:
    records = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user_id).all()
    count = len(records)
    for record in records:
        db.delete(record)
    db.commit()
    return count
