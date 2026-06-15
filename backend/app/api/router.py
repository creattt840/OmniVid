from fastapi import APIRouter

from app.api import (
    analysis_history,
    analyze,
    auth,
    billing,
    health,
    subtitles,
    upload,
    video,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(upload.router)
api_router.include_router(video.router)
api_router.include_router(subtitles.router)
api_router.include_router(analyze.router)
api_router.include_router(auth.router)
api_router.include_router(billing.router)
api_router.include_router(analysis_history.router)
