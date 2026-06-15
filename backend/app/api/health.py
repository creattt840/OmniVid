from fastapi import APIRouter

from app.services.container import get_downloader, get_video_analyzer

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check():
    downloader = get_downloader()
    return {
        "status": "ok",
        "message": "万能视频下载器服务运行中",
        "ffmpeg": downloader.has_ffmpeg,
        "ai_available": get_video_analyzer().is_ai_available(),
    }
