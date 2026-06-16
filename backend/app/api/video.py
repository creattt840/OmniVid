import asyncio
import os

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.schemas.video import DownloadRequest, ParseRequest
from app.services.container import get_bilibili_parser, get_douyin_parser, get_downloader
from app.services.video.bilibili import is_bilibili_url
from app.services.video.douyin import is_douyin_url
from app.services.video.url_validation import VideoUrlValidationError, validate_video_url
from app.services.video.ytdlp_utils import format_ytdlp_error

router = APIRouter(prefix="/api", tags=["video"])


@router.post("/parse")
async def parse_video(req: ParseRequest):
    try:
        url = validate_video_url(req.url)
    except VideoUrlValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": str(e)},
        )
    try:
        loop = asyncio.get_event_loop()
        if is_douyin_url(url):
            result = await loop.run_in_executor(None, get_douyin_parser().parse, url)
        elif is_bilibili_url(url):
            result = await loop.run_in_executor(None, get_bilibili_parser().parse, url)
        else:
            result = await loop.run_in_executor(None, get_downloader().parse_video, url)
        return {"success": True, "data": result}
    except Exception as e:
        err_msg = format_ytdlp_error(e, url=url)
        if "unsupported url" in err_msg.lower():
            err_msg = "无法识别为视频链接，请输入 B站、YouTube、抖音、TikTok 等平台的视频页面地址"
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"解析失败: {err_msg}"},
        )


@router.post("/download")
async def download_video(req: DownloadRequest):
    try:
        loop = asyncio.get_event_loop()
        if is_douyin_url(req.url):
            result = await loop.run_in_executor(None, get_douyin_parser().download, req.url)
        elif is_bilibili_url(req.url):
            result = await loop.run_in_executor(
                None, get_bilibili_parser().download, req.url, req.format_id
            )
        else:
            result = await loop.run_in_executor(
                None, get_downloader().download_video, req.url, req.format_id
            )
        filepath = result["filepath"]
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="下载的文件不存在")

        return FileResponse(
            path=filepath,
            filename=result["filename"],
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"下载失败: {format_ytdlp_error(e, url=req.url)}"},
        )


@router.post("/direct-url")
async def get_direct_url(req: DownloadRequest):
    try:
        loop = asyncio.get_event_loop()
        if is_bilibili_url(req.url):
            result = await loop.run_in_executor(
                None, get_bilibili_parser().get_direct_url, req.url, req.format_id
            )
        else:
            result = await loop.run_in_executor(
                None, get_downloader().get_direct_url, req.url, req.format_id
            )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": f"获取直链失败: {str(e)}"})


@router.get("/proxy/thumbnail")
async def proxy_thumbnail(url: str = Query(..., description="缩略图URL")):
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": url,
                },
            )
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            return StreamingResponse(
                iter([resp.content]),
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        raise HTTPException(status_code=502, detail="缩略图加载失败")
