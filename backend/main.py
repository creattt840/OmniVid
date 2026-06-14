import asyncio
import os
from contextlib import asynccontextmanager
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from bilibili import BilibiliParser, is_bilibili_url
from douyin import DouyinParser, is_douyin_url
from downloader import VideoDownloader
from subtitles import SubtitleFetcher, sanitize_filename
from transcriber import Transcriber
from summarizer import VideoAnalyzer

downloader = VideoDownloader()
douyin_parser = DouyinParser(download_dir=downloader.DOWNLOAD_DIR)
bilibili_parser = BilibiliParser(download_dir=downloader.DOWNLOAD_DIR)
subtitle_fetcher = SubtitleFetcher(downloader.DOWNLOAD_DIR, bilibili_parser)
transcriber = Transcriber(
    download_dir=downloader.DOWNLOAD_DIR,
    bilibili_parser=bilibili_parser,
    douyin_parser=douyin_parser,
    ffmpeg_path=downloader.ffmpeg_path,
    model_size=os.getenv("WHISPER_MODEL", "small"),
    max_duration=int(os.getenv("WHISPER_MAX_DURATION", "3600")),
)
video_analyzer = VideoAnalyzer(subtitle_fetcher, transcriber)


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


class AnalyzeRequest(BaseModel):
    url: str


class SubtitleDownloadRequest(BaseModel):
    url: str
    format: str = "srt"


class ChatRequest(BaseModel):
    message: str


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "message": "万能视频下载器服务运行中",
        "ffmpeg": downloader.has_ffmpeg,
        "ai_available": video_analyzer.is_ai_available(),
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


def _fetch_transcript_segments(url: str) -> tuple[list, dict, str]:
    """获取转录 segments，优先字幕，无字幕则 Whisper 兜底。"""
    segments, meta = subtitle_fetcher.fetch_from_url(url)
    source = "subtitle"
    if not segments:
        try:
            segments, meta = transcriber.transcribe_url(url)
            source = "whisper"
        except ValueError as e:
            raise ValueError(f"无法获取视频字幕：{e}") from e
    if not segments:
        raise ValueError("无法获取视频字幕（无字幕且语音转写失败）")
    return segments, meta, source


@app.post("/api/subtitles/download")
async def download_subtitles(req: SubtitleDownloadRequest):
    fmt = req.format.lower()
    if fmt not in ("srt", "vtt", "txt"):
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "format 仅支持 srt / vtt / txt"},
        )
    try:
        loop = asyncio.get_event_loop()
        segments, meta, source = await loop.run_in_executor(
            None, _fetch_transcript_segments, req.url
        )
        if fmt == "srt":
            content = SubtitleFetcher.segments_to_srt(segments)
            media_type = "application/x-subrip"
        elif fmt == "vtt":
            content = SubtitleFetcher.segments_to_vtt(segments)
            media_type = "text/vtt"
        else:
            content = SubtitleFetcher.segments_to_text(segments)
            media_type = "text/plain"

        title = meta.get("title") or "subtitle"
        filename = sanitize_filename(title, fmt)
        ascii_fallback = f"subtitle.{fmt}"
        content_disp = (
            f'attachment; filename="{ascii_fallback}"; '
            f"filename*=UTF-8''{quote(filename)}"
        )
        return StreamingResponse(
            iter([content.encode("utf-8")]),
            media_type=f"{media_type}; charset=utf-8",
            headers={
                "Content-Disposition": content_disp,
                "X-Transcript-Source": source,
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"字幕下载失败: {str(e)}"},
        )


@app.post("/api/analyze")
async def start_analyze(req: AnalyzeRequest):
    try:
        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None, video_analyzer.prepare_transcript, req.url
        )
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
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"分析准备失败: {str(e)}"},
        )


@app.get("/api/analyze/{session_id}/stream")
async def stream_analyze(session_id: str):
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


@app.post("/api/analyze/{session_id}/chat")
async def chat_analyze(session_id: str, req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail={"success": False, "error": "消息不能为空"})

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
