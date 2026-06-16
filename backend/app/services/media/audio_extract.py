"""FFmpeg 音频抽取：为 Whisper 生成 16kHz 单声道 MP3。"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("audio_extract")


def _resolve_ffmpeg(ffmpeg_path: Optional[str] = None) -> Optional[str]:
    if ffmpeg_path:
        name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        candidate = os.path.join(ffmpeg_path, name)
        if os.path.isfile(candidate):
            return candidate
    return shutil.which("ffmpeg")


def extract_audio_for_whisper(
    input_path: Path,
    output_path: Path,
    ffmpeg_path: Optional[str] = None,
) -> Path:
    """
    从视频/音频文件抽取 16kHz 单声道 MP3，供 Whisper 使用。
    FFmpeg 不可用时返回原文件路径。
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    ffmpeg = _resolve_ffmpeg(ffmpeg_path)
    if not ffmpeg:
        logger.warning("FFmpeg 不可用，跳过音频抽取: %s", input_path.name)
        return input_path

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-b:a",
        "64k",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        logger.warning("FFmpeg 抽音失败，使用原文件: %s", e)
    return input_path
