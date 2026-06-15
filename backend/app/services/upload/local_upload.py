"""本地视频/音频上传：存储、元数据提取、TTL 管理"""

import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

logger = logging.getLogger("local_upload")

UPLOAD_TTL = 30 * 60  # 30 minutes

MEDIA_EXTENSIONS = frozenset({
    "mp4", "mkv", "mov", "webm", "avi", "mp3", "m4a", "wav", "aac", "ogg",
})
SUBTITLE_EXTENSIONS = frozenset({"srt", "vtt"})
AUDIO_EXTENSIONS = frozenset({"mp3", "m4a", "wav", "aac", "ogg"})

MEDIA_MIME = {
    "mp4": "video/mp4",
    "mkv": "video/x-matroska",
    "mov": "video/quicktime",
    "webm": "video/webm",
    "avi": "video/x-msvideo",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
}


@dataclass
class UploadRecord:
    file_id: str
    media_path: Path
    title: str
    duration: int
    ext: str
    filesize: int
    width: int = 0
    height: int = 0
    subtitle_path: Optional[Path] = None
    created_at: float = field(default_factory=time.time)

    @property
    def is_audio(self) -> bool:
        return self.ext in AUDIO_EXTENSIONS


class UploadStore:
    def __init__(self):
        self._records: dict[str, UploadRecord] = {}

    def add(self, record: UploadRecord) -> UploadRecord:
        self.cleanup_expired()
        self._records[record.file_id] = record
        return record

    def get(self, file_id: str) -> Optional[UploadRecord]:
        self.cleanup_expired()
        return self._records.get(file_id)

    def cleanup_expired(self):
        now = time.time()
        expired = [
            fid for fid, rec in self._records.items()
            if now - rec.created_at > UPLOAD_TTL
        ]
        for fid in expired:
            self._remove_record(fid)

    def _remove_record(self, file_id: str):
        rec = self._records.pop(file_id, None)
        if rec and rec.media_path.parent.exists():
            try:
                shutil.rmtree(rec.media_path.parent, ignore_errors=True)
            except OSError:
                pass

    def cleanup_all(self):
        for fid in list(self._records.keys()):
            self._remove_record(fid)


upload_store = UploadStore()


class LocalUploadHandler:
    def __init__(
        self,
        download_dir: str,
        ffmpeg_path: Optional[str] = None,
        max_size_mb: int = 500,
        max_duration: int = 3600,
    ):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_duration = max_duration

    @staticmethod
    def _ext(filename: str) -> str:
        return Path(filename or "").suffix.lstrip(".").lower()

    @staticmethod
    def _title_from_filename(filename: str) -> str:
        stem = Path(filename).stem
        return re.sub(r'[\\/*?:"<>|]', "_", stem).strip() or "本地视频"

    def _ffprobe_path(self) -> Optional[str]:
        if self.ffmpeg_path:
            candidate = os.path.join(self.ffmpeg_path, "ffprobe.exe" if os.name == "nt" else "ffprobe")
            if os.path.isfile(candidate):
                return candidate
            candidate = os.path.join(self.ffmpeg_path, "ffprobe")
            if os.path.isfile(candidate):
                return candidate
        return shutil.which("ffprobe")

    def extract_metadata(self, file_path: Path) -> dict:
        """ffprobe 提取 duration / 分辨率；失败时返回空字段。"""
        meta = {"duration": 0, "width": 0, "height": 0}
        ffprobe = self._ffprobe_path()
        if not ffprobe:
            return meta
        try:
            result = subprocess.run(
                [
                    ffprobe,
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                return meta
            data = json.loads(result.stdout or "{}")
            fmt = data.get("format") or {}
            meta["duration"] = int(float(fmt.get("duration") or 0))
            for stream in data.get("streams") or []:
                if stream.get("codec_type") == "video":
                    meta["width"] = int(stream.get("width") or 0)
                    meta["height"] = int(stream.get("height") or 0)
                    break
        except Exception:
            logger.exception("ffprobe 元数据提取失败")
        return meta

    @staticmethod
    def _format_duration(seconds: int) -> str:
        if not seconds:
            return "00:00"
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def _format_filesize(size: int) -> str:
        if size < 1024 * 1024:
            return f"{size / 1024:.0f}KB"
        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f}MB"
        return f"{size / (1024 * 1024 * 1024):.2f}GB"

    async def save_upload(
        self,
        media: UploadFile,
        subtitle: Optional[UploadFile] = None,
    ) -> dict:
        media_ext = self._ext(media.filename)
        if media_ext not in MEDIA_EXTENSIONS:
            raise ValueError(
                f"不支持的媒体格式 .{media_ext}，"
                f"支持：{', '.join(sorted(MEDIA_EXTENSIONS))}"
            )

        media_data = await media.read()
        if len(media_data) > self.max_size_bytes:
            raise ValueError(
                f"文件大小 {self._format_filesize(len(media_data))} 超过上限 "
                f"{self.max_size_bytes // (1024 * 1024)}MB"
            )
        if not media_data:
            raise ValueError("上传文件为空")

        file_id = str(uuid.uuid4())
        upload_dir = self.download_dir / f"upload_{file_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)

        media_path = upload_dir / f"media.{media_ext}"
        media_path.write_bytes(media_data)

        probe = self.extract_metadata(media_path)
        duration = probe["duration"]
        if duration > self.max_duration:
            shutil.rmtree(upload_dir, ignore_errors=True)
            raise ValueError(
                f"视频时长 {duration // 60} 分钟超过上限 ({self.max_duration // 60} 分钟)"
            )

        subtitle_path = None
        if subtitle and subtitle.filename:
            sub_ext = self._ext(subtitle.filename)
            if sub_ext not in SUBTITLE_EXTENSIONS:
                shutil.rmtree(upload_dir, ignore_errors=True)
                raise ValueError(
                    f"不支持的字幕格式 .{sub_ext}，支持：srt, vtt"
                )
            sub_data = await subtitle.read()
            if sub_data:
                subtitle_path = upload_dir / f"subtitle.{sub_ext}"
                subtitle_path.write_bytes(sub_data)

        title = self._title_from_filename(media.filename or "本地视频")
        record = UploadRecord(
            file_id=file_id,
            media_path=media_path,
            title=title,
            duration=duration,
            ext=media_ext,
            filesize=len(media_data),
            width=probe["width"],
            height=probe["height"],
            subtitle_path=subtitle_path,
        )
        upload_store.add(record)
        return self.build_parse_response(record)

    def build_parse_response(self, record: UploadRecord) -> dict:
        height = record.height or (0 if record.is_audio else 720)
        resolution = f"{height}p" if height else "音频"
        label = f"{resolution} · {record.ext.upper()}"
        if record.is_audio:
            label = f"音频 · {record.ext.upper()}"

        return {
            "id": record.file_id,
            "file_id": record.file_id,
            "title": record.title,
            "thumbnail": None,
            "duration": record.duration,
            "duration_string": self._format_duration(record.duration),
            "uploader": "本地文件",
            "platform": "本地文件",
            "view_count": None,
            "upload_date": "",
            "description": "",
            "filesize": record.filesize,
            "filesize_string": self._format_filesize(record.filesize),
            "has_subtitle_file": record.subtitle_path is not None,
            "formats": [{
                "format_id": "local",
                "ext": record.ext,
                "resolution": resolution,
                "height": height,
                "label": label,
                "has_audio": True,
                "filesize": record.filesize,
            }],
            "subtitles": ["外挂字幕"] if record.subtitle_path else [],
            "automatic_captions": [],
        }

    def get_media_type(self, record: UploadRecord) -> str:
        return MEDIA_MIME.get(record.ext, "application/octet-stream")
