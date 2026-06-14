import asyncio
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from bilibili import BilibiliParser, is_bilibili_url
from douyin import DouyinParser, is_douyin_url
from downloader import VideoDownloader

downloader = VideoDownloader()
douyin_parser = DouyinParser(download_dir=downloader.DOWNLOAD_DIR)
bilibili_parser = BilibiliParser(download_dir=downloader.DOWNLOAD_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    download_dir = downloader.DOWNLOAD_DIR
    if os.path.exists(download_dir):
        for f in os.listdir(download_dir):
            try:
                os.remove(os.path.join(download_dir, f))
            except OSError:
                pass


app = FastAPI(
    title="万能视频下载器 API",
    description="基于 yt-dlp 的万能视频下载服务，支持 1800+ 平台",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format_id: str = "bestvideo+bestaudio/best"


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "message": "万能视频下载器服务运行中",
        "ffmpeg": downloader.has_ffmpeg,
    }


@app.post("/api/parse")
async def parse_video(req: ParseRequest):
    try:
        loop = asyncio.get_event_loop()
        if is_douyin_url(req.url):
            result = await loop.run_in_executor(None, douyin_parser.parse, req.url)
        elif is_bilibili_url(req.url):
            result = await loop.run_in_executor(None, bilibili_parser.parse, req.url)
        else:
            result = await loop.run_in_executor(None, downloader.parse_video, req.url)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": f"解析失败: {str(e)}"})


@app.post("/api/download")
async def download_video(req: DownloadRequest):
    try:
        loop = asyncio.get_event_loop()
        if is_douyin_url(req.url):
            result = await loop.run_in_executor(None, douyin_parser.download, req.url)
        elif is_bilibili_url(req.url):
            result = await loop.run_in_executor(
                None, bilibili_parser.download, req.url, req.format_id
            )
        else:
            result = await loop.run_in_executor(
                None, downloader.download_video, req.url, req.format_id
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
        raise HTTPException(status_code=400, detail={"success": False, "error": f"下载失败: {str(e)}"})


@app.post("/api/direct-url")
async def get_direct_url(req: DownloadRequest):
    try:
        loop = asyncio.get_event_loop()
        if is_bilibili_url(req.url):
            result = await loop.run_in_executor(
                None, bilibili_parser.get_direct_url, req.url, req.format_id
            )
        else:
            result = await loop.run_in_executor(
                None, downloader.get_direct_url, req.url, req.format_id
            )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": f"获取直链失败: {str(e)}"})


@app.get("/api/proxy/thumbnail")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
