import asyncio
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_current_user
from app.db.models import User
from app.schemas.subtitles import SubtitleDownloadRequest, TranslateRequest
from app.services.ai.subtitles import SubtitleFetcher, sanitize_filename
from app.services.container import get_subtitle_fetcher, get_transcriber, get_video_analyzer

router = APIRouter(prefix="/api/subtitles", tags=["subtitles"])


def _fetch_transcript_segments(url: str) -> tuple[list, dict, str]:
    """获取转录 segments，优先字幕，无字幕则 Whisper 兜底。"""
    subtitle_fetcher = get_subtitle_fetcher()
    transcriber = get_transcriber()
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


@router.post("/download")
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


@router.post("/translate")
async def translate_subtitles(req: TranslateRequest, user: User = Depends(get_current_user)):
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
    video_analyzer = get_video_analyzer()
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
