import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import User
from app.schemas.analyze import AnalyzeRequest, ChatRequest
from app.services.container import get_video_analyzer
from app.services.membership import check_ai_quota, consume_ai_quota
from app.services.upload.local_upload import upload_store

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post("")
async def start_analyze(
    req: AnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed, quota_msg = check_ai_quota(db, user)
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": quota_msg,
                "code": "QUOTA_EXCEEDED",
            },
        )
    video_analyzer = get_video_analyzer()
    try:
        loop = asyncio.get_event_loop()
        if req.file_id:
            record = upload_store.get(req.file_id.strip())
            if not record:
                raise ValueError("上传文件不存在或已过期，请重新上传")
            session = await loop.run_in_executor(
                None, video_analyzer.prepare_transcript_from_file, record
            )
        else:
            session = await loop.run_in_executor(
                None, video_analyzer.prepare_transcript, req.url.strip()
            )
        consume_ai_quota(db, user)
        return {
            "success": True,
            "data": {
                "session_id": session.session_id,
                "title": session.title,
                "transcript_source": session.transcript_source,
                "segment_count": len(session.segments),
                "duration": session.duration,
                "platform": session.platform,
                "ai_available": video_analyzer.is_ai_available(),
            },
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"分析准备失败: {str(e)}"},
        )


@router.get("/{session_id}/stream")
async def stream_analyze(session_id: str):
    video_analyzer = get_video_analyzer()

    def event_generator():
        for event in video_analyzer.stream_summary(session_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{session_id}/rewrite")
async def rewrite_analyze(session_id: str, user: User = Depends(get_current_user)):
    video_analyzer = get_video_analyzer()

    def event_generator():
        for event in video_analyzer.stream_rewrite(session_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/chat")
async def chat_analyze(session_id: str, req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail={"success": False, "error": "消息不能为空"})

    video_analyzer = get_video_analyzer()

    def event_generator():
        for event in video_analyzer.stream_chat(session_id, req.message.strip()):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
