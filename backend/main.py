import asyncio
import os
import shutil
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

import httpx
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, model_validator

from bilibili import BilibiliParser, is_bilibili_url
from douyin import DouyinParser, is_douyin_url
from downloader import VideoDownloader
from ytdlp_utils import format_ytdlp_error
from local_upload import LocalUploadHandler, upload_store
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
local_upload_handler = LocalUploadHandler(
    download_dir=downloader.DOWNLOAD_DIR,
    ffmpeg_path=downloader.ffmpeg_path,
    max_size_mb=int(os.getenv("UPLOAD_MAX_SIZE_MB", "500")),
    max_duration=int(os.getenv("UPLOAD_MAX_DURATION", os.getenv("WHISPER_MAX_DURATION", "3600"))),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    upload_store.cleanup_all()
    download_dir = downloader.DOWNLOAD_DIR
    if os.path.exists(download_dir):
        for name in os.listdir(download_dir):
            path = os.path.join(download_dir, name)
            try:
                if os.path.isdir(path) and name.startswith("upload_"):
                    shutil.rmtree(path, ignore_errors=True)
                elif os.path.isfile(path):
                    os.remove(path)
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
    url: Optional[str] = None
    file_id: Optional[str] = None

    @model_validator(mode="after")
    def check_one_of(self):
        has_url = bool(self.url and self.url.strip())
        has_file = bool(self.file_id and self.file_id.strip())
        if has_url == has_file:
            raise ValueError("请提供 url 或 file_id 其中之一")
        return self


class SubtitleDownloadRequest(BaseModel):
    url: str
    format: str = "srt"


class ChatRequest(BaseModel):
    message: str


class TranslateRequest(BaseModel):
    url: str
    target_lang: str = "en"
    format: str = "srt"


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "message": "万能视频下载器服务运行中",
        "ffmpeg": downloader.has_ffmpeg,
        "ai_available": video_analyzer.is_ai_available(),
    }


@app.post("/api/upload")
async def upload_local_file(
    media: UploadFile = File(...),
    subtitle: Optional[UploadFile] = File(None),
):
    try:
        data = await local_upload_handler.save_upload(media, subtitle)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": str(e)})
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"上传失败: {str(e)}"},
        )


@app.get("/api/upload/{file_id}/stream")
async def stream_uploaded_file(file_id: str):
    record = upload_store.get(file_id)
    if not record or not record.media_path.exists():
        raise HTTPException(status_code=404, detail={"success": False, "error": "文件不存在或已过期"})
    return FileResponse(
        path=str(record.media_path),
        media_type=local_upload_handler.get_media_type(record),
        filename=f"{record.title}.{record.ext}",
    )


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
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"解析失败: {format_ytdlp_error(e, url=req.url)}"},
        )


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
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"下载失败: {format_ytdlp_error(e, url=req.url)}"},
        )


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


@app.get("/api/analyze/{session_id}/rewrite")
async def rewrite_analyze(session_id: str):
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


@app.post("/api/subtitles/translate")
async def translate_subtitles(req: TranslateRequest):
    fmt = req.format.lower()
    if fmt not in ("srt", "vtt", "txt"):
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "format 仅支持 srt / vtt / txt"},
        )
    lang = req.target_lang.lower()
    if lang not in ("en", "zh", "ja", "ko", "es", "fr"):
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "target_lang 仅支持 en/zh/ja/ko/es/fr"},
        )
    if not video_analyzer.is_ai_available():
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "未配置 DEEPSEEK_API_KEY，无法翻译"},
        )
    try:
        loop = asyncio.get_event_loop()
        segments, meta, source = await loop.run_in_executor(
            None, _fetch_transcript_segments, req.url
        )
        translated = await loop.run_in_executor(
            None, video_analyzer.translate_segments, segments, lang
        )
        if fmt == "srt":
            content = SubtitleFetcher.segments_to_srt(translated)
            media_type = "application/x-subrip"
        elif fmt == "vtt":
            content = SubtitleFetcher.segments_to_vtt(translated)
            media_type = "text/vtt"
        else:
            content = SubtitleFetcher.segments_to_text(translated)
            media_type = "text/plain"

        title = meta.get("title") or "subtitle"
        lang_suffix = f"_{lang}"
        filename = sanitize_filename(f"{title}{lang_suffix}", fmt)
        ascii_fallback = f"subtitle{lang_suffix}.{fmt}"
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
                "X-Target-Lang": lang,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": str(e)})
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": f"字幕翻译失败: {str(e)}"},
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
