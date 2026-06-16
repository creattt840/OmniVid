"""无字幕视频 ASR：下载音频 + faster-whisper 转写"""

import logging
import re
import threading
import time
from pathlib import Path
from typing import Optional

from app.services.media.audio_extract import extract_audio_for_whisper
from app.services.video.metadata_cache import get_bilibili, get_douyin, get_ytdlp_info, put_bilibili, put_douyin
from app.services.video.ytdlp_utils import download_from_info, extract_info as ytdlp_extract_info

from app.services.video.bilibili import BilibiliParser, is_bilibili_url
from app.services.video.douyin import DouyinParser, is_douyin_url

logger = logging.getLogger("transcriber")

_whisper_lock = threading.Lock()
_whisper_model = None

# 过滤幻听片段：no_speech 概率高或置信度过低
_NO_SPEECH_THRESHOLD = 0.6
_MIN_AVG_LOGPROB = -1.0


def _filter_whisper_segments(segments_iter) -> list[dict]:
    segments = []
    for seg in segments_iter:
        text = seg.text.strip()
        if not text:
            continue
        no_speech = getattr(seg, "no_speech_prob", 0.0) or 0.0
        avg_logprob = getattr(seg, "avg_logprob", 0.0) or 0.0
        if no_speech > _NO_SPEECH_THRESHOLD:
            continue
        if avg_logprob < _MIN_AVG_LOGPROB:
            continue
        segments.append({"start": seg.start, "end": seg.end, "text": text})
    return segments


def _get_whisper_model(model_size: str = "small"):
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _whisper_model


def warmup_whisper(model_size: str = "small") -> None:
    """后台预加载 Whisper 模型，避免首请求冷启动。"""

    def _run():
        try:
            with _whisper_lock:
                _get_whisper_model(model_size)
            logger.info("Whisper 模型预热完成: %s", model_size)
        except Exception:
            logger.exception("Whisper 模型预热失败")

    threading.Thread(target=_run, daemon=True).start()


class Transcriber:
    def __init__(
        self,
        download_dir: str,
        bilibili_parser: BilibiliParser,
        douyin_parser: DouyinParser,
        ffmpeg_path: Optional[str] = None,
        model_size: str = "small",
        max_duration: int = 3600,
        beam_size: int = 1,
    ):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.bilibili = bilibili_parser
        self.douyin = douyin_parser
        self.ffmpeg_path = ffmpeg_path
        self.model_size = model_size
        self.max_duration = max_duration
        self.beam_size = beam_size

    def _run_whisper(self, file_path: Path) -> tuple[list[dict], object]:
        with _whisper_lock:
            model = _get_whisper_model(self.model_size)
            segments_iter, info = model.transcribe(
                str(file_path),
                beam_size=self.beam_size,
                language=None,
                vad_filter=True,
            )
            segments = _filter_whisper_segments(segments_iter)
        return segments, info

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

        t0 = time.perf_counter()
        try:
            segments, info = self._run_whisper(file_path)
            whisper_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(
                "transcribe_file whisper_ms=%d beam_size=%d",
                whisper_ms,
                self.beam_size,
            )
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
        total_t0 = time.perf_counter()
        audio_path, meta, cleanup_paths = self._download_audio(url)
        download_ms = int((time.perf_counter() - total_t0) * 1000)

        if not audio_path:
            raise ValueError("无法下载音频进行转写")

        duration = meta.get("duration") or 0
        if duration > self.max_duration:
            self._cleanup_paths(cleanup_paths)
            raise ValueError(
                f"视频时长 {duration // 60} 分钟超过 ASR 上限 ({self.max_duration // 60} 分钟)"
            )

        whisper_ms = 0
        try:
            t1 = time.perf_counter()
            segments, info = self._run_whisper(audio_path)
            whisper_ms = int((time.perf_counter() - t1) * 1000)
            if not meta.get("duration") and info:
                meta["duration"] = int(info.duration or 0)
            if not segments:
                raise ValueError("语音转写未识别到有效文本，请尝试其他视频")

            total_ms = int((time.perf_counter() - total_t0) * 1000)
            logger.info(
                "transcribe_url platform=%s download_ms=%d whisper_ms=%d total_ms=%d beam_size=%d",
                meta.get("platform"),
                download_ms,
                whisper_ms,
                total_ms,
                self.beam_size,
            )
            return segments, meta
        except ValueError:
            raise
        except Exception as e:
            logger.exception("Whisper 转写失败")
            raise ValueError(f"语音转写失败: {e}") from e
        finally:
            self._cleanup_paths(cleanup_paths)

    @staticmethod
    def _cleanup_paths(paths: list[Path]) -> None:
        seen = set()
        for path in paths:
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            path.unlink(missing_ok=True)

    def _download_audio(self, url: str) -> tuple[Optional[Path], dict, list[Path]]:
        """返回 (whisper输入路径, meta, 需清理的临时文件列表)。"""
        if is_bilibili_url(url):
            return self._download_bilibili_audio(url)
        if is_douyin_url(url):
            return self._download_douyin_audio(url)
        return self._download_ytdlp_audio(url)

    def _prepare_audio_file(
        self,
        raw_path: Path,
        output_stem: str,
        needs_extract: bool,
    ) -> tuple[Path, list[Path]]:
        cleanup: list[Path] = [raw_path]
        if not needs_extract:
            return raw_path, cleanup

        mp3_path = self.download_dir / f"{output_stem}_16k.mp3"
        extracted = extract_audio_for_whisper(raw_path, mp3_path, self.ffmpeg_path)
        if extracted != raw_path and extracted.exists():
            cleanup.append(extracted)
            return extracted, cleanup
        return raw_path, cleanup

    def _download_bilibili_audio(self, url: str) -> tuple[Optional[Path], dict, list[Path]]:
        ctx = get_bilibili(url)
        if ctx:
            view_data = ctx["view_data"]
            cid = ctx["cid"]
            bvid = ctx.get("bvid")
            aid = ctx["aid"]
        else:
            share_url = self.bilibili._extract_url(url)
            resolved = self.bilibili._resolve_redirect(share_url)
            bvid, aid, page = self.bilibili._parse_video_id(resolved)
            view_data = self.bilibili._fetch_view(bvid=bvid, aid=aid)
            cid = self.bilibili._resolve_cid(view_data, page)
            aid = view_data["aid"]
            put_bilibili(
                url,
                view_data=view_data,
                cid=cid,
                bvid=bvid,
                aid=aid,
                page=page,
            )

        meta = {
            "title": view_data.get("title") or "未知标题",
            "duration": view_data.get("duration") or 0,
            "platform": "哔哩哔哩",
        }

        play_data = self.bilibili._fetch_playurl(aid, cid, 16, bvid)
        media_url, needs_extract = self.bilibili._get_audio_url(play_data)
        if not media_url:
            return None, meta, []

        safe = re.sub(r'[\\/*?:"<>|]', "_", meta["title"])[:40]
        ext = "m4a" if not needs_extract else "mp4"
        raw_path = self.download_dir / f"{safe}_audio.{ext}"
        referer = f"https://www.bilibili.com/video/{bvid}" if bvid else "https://www.bilibili.com/"
        self.bilibili._download_file(media_url, raw_path, referer)

        audio_path, cleanup = self._prepare_audio_file(raw_path, safe, needs_extract)
        return audio_path, meta, cleanup

    def _download_douyin_audio(self, url: str) -> tuple[Optional[Path], dict, list[Path]]:
        ctx = get_douyin(url)
        if not ctx:
            info = self.douyin.parse(url)
            ctx = get_douyin(url)
            if not ctx:
                share_url = self.douyin._extract_url(url)
                resolved_url = self.douyin._resolve_redirect(share_url)
                video_id = self.douyin._extract_video_id(resolved_url)
                item_info = self.douyin._fetch_item_info(video_id, resolved_url)
                put_douyin(url, item_info=item_info, video_id=video_id)
                ctx = {"item_info": item_info, "video_id": video_id}
            meta = {
                "title": info.get("title") or "未知标题",
                "duration": info.get("duration") or 0,
                "platform": "抖音",
            }
        else:
            item_info = ctx["item_info"]
            meta = {
                "title": item_info.get("desc") or "未知标题",
                "duration": self._douyin_duration(item_info),
                "platform": "抖音",
            }

        item_info = ctx["item_info"]
        video_id = ctx["video_id"]

        media_url = self.douyin._get_media_url(item_info, mode="video")
        title = meta["title"]
        safe = re.sub(r'[\\/*?:"<>|\n\r\t#@]', "_", title).strip("_. ")[:40] or f"douyin_{video_id}"
        raw_path = self.download_dir / f"{safe}.mp4"
        self.douyin._download_file(media_url, raw_path)

        audio_path, cleanup = self._prepare_audio_file(raw_path, safe, needs_extract=True)
        return audio_path, meta, cleanup

    @staticmethod
    def _douyin_duration(item_info: dict) -> int:
        duration = item_info.get("video", {}).get("duration", 0)
        return duration // 1000 if duration > 1000 else duration

    def _download_ytdlp_audio(self, url: str) -> tuple[Optional[Path], dict, list[Path]]:
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

        cached_info = get_ytdlp_info(url)
        if cached_info:
            info = download_from_info(url, cached_info, **ydl_opts)
        else:
            info = ytdlp_extract_info(url, download=True, **ydl_opts)
        if not info:
            return None, {}, []

        meta = {
            "title": info.get("title") or "未知标题",
            "duration": info.get("duration") or 0,
            "platform": info.get("extractor", info.get("extractor_key", "Unknown")),
        }

        vid = info.get("id", "unknown")
        mp3_path = self.download_dir / f"audio_{vid}.mp3"
        if mp3_path.exists():
            return mp3_path, meta, [mp3_path]

        for f in self.download_dir.glob(f"audio_{vid}.*"):
            return f, meta, [f]

        ext = info.get("ext", "mp3")
        alt_path = self.download_dir / f"audio_{vid}.{ext}"
        if alt_path.exists():
            return alt_path, meta, [alt_path]

        return None, meta, []
