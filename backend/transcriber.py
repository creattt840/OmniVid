"""无字幕视频 ASR：下载音频 + faster-whisper 转写"""

import logging
import os
import re
import threading
from pathlib import Path
from typing import Optional

from ytdlp_utils import extract_info as ytdlp_extract_info

from bilibili import BilibiliParser, is_bilibili_url
from douyin import DouyinParser, is_douyin_url

logger = logging.getLogger("transcriber")

_whisper_lock = threading.Lock()
_whisper_model = None


def _get_whisper_model(model_size: str = "small"):
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _whisper_model


class Transcriber:
    def __init__(
        self,
        download_dir: str,
        bilibili_parser: BilibiliParser,
        douyin_parser: DouyinParser,
        ffmpeg_path: Optional[str] = None,
        model_size: str = "small",
        max_duration: int = 3600,
    ):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.bilibili = bilibili_parser
        self.douyin = douyin_parser
        self.ffmpeg_path = ffmpeg_path
        self.model_size = model_size
        self.max_duration = max_duration

    def transcribe_file(self, file_path: Path, meta: Optional[dict] = None) -> tuple[list[dict], dict]:
        """对本地音视频文件 Whisper 转写。"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise ValueError("本地文件不存在")

        base_meta = {
            "title": meta.get("title") if meta else file_path.stem,
            "duration": meta.get("duration", 0) if meta else 0,
            "platform": "本地文件",
        }

        duration = base_meta["duration"]
        if duration > self.max_duration:
            raise ValueError(
                f"视频时长 {duration // 60} 分钟超过 ASR 上限 ({self.max_duration // 60} 分钟)"
            )

        try:
            with _whisper_lock:
                model = _get_whisper_model(self.model_size)
                segments_iter, info = model.transcribe(
                    str(file_path),
                    beam_size=5,
                    language=None,
                    vad_filter=False,
                )
                segments = [
                    {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
                    for seg in segments_iter
                    if seg.text.strip()
                ]
            if not base_meta.get("duration") and info:
                base_meta["duration"] = int(info.duration or 0)
            if not segments:
                raise ValueError("语音转写未识别到有效文本，请尝试其他视频")
            return segments, base_meta
        except ValueError:
            raise
        except Exception as e:
            logger.exception("Whisper 本地文件转写失败")
            raise ValueError(f"语音转写失败: {e}") from e

    def transcribe_url(self, url: str) -> tuple[list[dict], dict]:
        """
        下载音频并转写。
        返回 (segments, meta)。
        """
        audio_path, meta = self._download_audio(url)
        if not audio_path:
            raise ValueError("无法下载音频进行转写")

        duration = meta.get("duration") or 0
        if duration > self.max_duration:
            audio_path.unlink(missing_ok=True)
            raise ValueError(
                f"视频时长 {duration // 60} 分钟超过 ASR 上限 ({self.max_duration // 60} 分钟)"
            )

        try:
            with _whisper_lock:
                model = _get_whisper_model(self.model_size)
                segments_iter, info = model.transcribe(
                    str(audio_path),
                    beam_size=5,
                    language=None,
                    vad_filter=False,
                )
                segments = [
                    {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
                    for seg in segments_iter
                    if seg.text.strip()
                ]
            if not meta.get("duration") and info:
                meta["duration"] = int(info.duration or 0)
            if not segments:
                raise ValueError("语音转写未识别到有效文本，请尝试其他视频")
            return segments, meta
        except ValueError:
            raise
        except Exception as e:
            logger.exception("Whisper 转写失败")
            raise ValueError(f"语音转写失败: {e}") from e
        finally:
            audio_path.unlink(missing_ok=True)

    def _download_audio(self, url: str) -> tuple[Optional[Path], dict]:
        if is_bilibili_url(url):
            return self._download_bilibili_audio(url)
        if is_douyin_url(url):
            return self._download_douyin_audio(url)
        return self._download_ytdlp_audio(url)

    def _download_bilibili_audio(self, url: str) -> tuple[Optional[Path], dict]:
        share_url = self.bilibili._extract_url(url)
        resolved = self.bilibili._resolve_redirect(share_url)
        bvid, aid, page = self.bilibili._parse_video_id(resolved)
        view_data = self.bilibili._fetch_view(bvid=bvid, aid=aid)
        cid = self.bilibili._resolve_cid(view_data, page)
        aid = view_data["aid"]

        meta = {
            "title": view_data.get("title") or "未知标题",
            "duration": view_data.get("duration") or 0,
            "platform": "哔哩哔哩",
        }

        play_data = self.bilibili._fetch_playurl(aid, cid, 16, bvid)
        media_url = self.bilibili._get_media_url(play_data)
        if not media_url:
            return None, meta

        safe = re.sub(r'[\\/*?:"<>|]', "_", meta["title"])[:40]
        out_path = self.download_dir / f"{safe}_audio.mp4"
        referer = f"https://www.bilibili.com/video/{bvid}" if bvid else "https://www.bilibili.com/"
        self.bilibili._download_file(media_url, out_path, referer)
        return out_path, meta

    def _download_douyin_audio(self, url: str) -> tuple[Optional[Path], dict]:
        info = self.douyin.parse(url)
        meta = {
            "title": info.get("title") or "未知标题",
            "duration": info.get("duration") or 0,
            "platform": "抖音",
        }
        result = self.douyin.download(url)
        filepath = Path(result["filepath"])
        return filepath, meta

    def _download_ytdlp_audio(self, url: str) -> tuple[Optional[Path], dict]:
        outtmpl = str(self.download_dir / "audio_%(id)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }],
        }
        if self.ffmpeg_path:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_path

        info = ytdlp_extract_info(url, download=True, **ydl_opts)
        if not info:
            return None, {}

        meta = {
            "title": info.get("title") or "未知标题",
            "duration": info.get("duration") or 0,
            "platform": info.get("extractor", info.get("extractor_key", "Unknown")),
        }

        vid = info.get("id", "unknown")
        mp3_path = self.download_dir / f"audio_{vid}.mp3"
        if mp3_path.exists():
            return mp3_path, meta

        for f in self.download_dir.glob(f"audio_{vid}.*"):
            return f, meta

        ext = info.get("ext", "mp3")
        alt_path = self.download_dir / f"audio_{vid}.{ext}"
        if alt_path.exists():
            return alt_path, meta

        return None, meta
