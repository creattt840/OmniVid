import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import User
from app.schemas.analysis_history import SaveHistoryRequest
from app.schemas.analyze import ChatRequest
from app.services.analysis_history import (
    clear_history,
    delete_history,
    get_history_record,
    list_history,
    save_history,
    update_article_content,
    update_chat_history,
)
from app.services.container import get_video_analyzer

router = APIRouter(prefix="/api/analysis-history", tags=["analysis-history"])


def _payload_from_request(req: SaveHistoryRequest) -> dict:
    data = {
        "url": req.url,
        "source": req.source,
        "partial": req.partial or False,
    }
    if req.title is not None:
        data["title"] = req.title
    if req.platform is not None:
        data["platform"] = req.platform
    if req.thumbnail is not None:
        data["thumbnail"] = req.thumbnail
    if req.summary is not None:
        data["summary"] = req.summary
    if req.mindmap is not None:
        data["mindmap"] = req.mindmap
    if req.segments is not None:
        data["segments"] = req.segments
    if req.article is not None:
        data["article"] = req.article
    if req.chatHistory is not None:
        data["chatHistory"] = req.chatHistory
    if req.transcriptSource is not None:
        data["transcriptSource"] = req.transcriptSource
    return data


@router.get("")
def get_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": list_history(db, user.id)}


@router.post("")
def create_history(
    req: SaveHistoryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = save_history(db, user, _payload_from_request(req))
    return {"success": True, "data": item}


@router.post("/{history_id}/chat")
async def history_chat(
    history_id: int,
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail={"success": False, "error": "消息不能为空"})

    record = get_history_record(db, user.id, history_id)
    if not record:
        raise HTTPException(status_code=404, detail={"success": False, "error": "历史记录不存在"})

    video_analyzer = get_video_analyzer()
    chat_history = list(record.chat_history_json or [])

    def event_generator():
        for event in video_analyzer.stream_chat_from_context(
            title=record.title,
            segments=record.segments_json or [],
            summary=record.summary_json,
            chat_history=chat_history,
            message=req.message.strip(),
        ):
            yield event
        update_chat_history(db, user.id, history_id, chat_history)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{history_id}/rewrite")
async def history_rewrite(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = get_history_record(db, user.id, history_id)
    if not record:
        raise HTTPException(status_code=404, detail={"success": False, "error": "历史记录不存在"})

    video_analyzer = get_video_analyzer()
    article_holder: dict[str, str] = {"content": ""}

    def event_generator():
        for event in video_analyzer.stream_rewrite_from_context(
            title=record.title,
            segments=record.segments_json or [],
        ):
            if event.startswith("data: "):
                try:
                    payload = json.loads(event[6:].strip())
                    if payload.get("type") == "rewrite_done":
                        article_holder["content"] = payload.get("content") or ""
                except json.JSONDecodeError:
                    pass
            yield event
        if article_holder["content"]:
            update_article_content(db, user.id, history_id, article_holder["content"])

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/{history_id}")
def remove_history(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not delete_history(db, user.id, history_id):
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": "历史记录不存在"},
        )
    return {"success": True, "data": None}


@router.delete("")
def remove_all_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    deleted = clear_history(db, user.id)
    return {"success": True, "data": {"deleted": deleted}}
