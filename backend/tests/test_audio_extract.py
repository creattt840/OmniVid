"""FFmpeg 音频抽取单元测试。"""
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.media.audio_extract import extract_audio_for_whisper


def test_extract_skips_when_ffmpeg_missing(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake")
    output_file = tmp_path / "out.mp3"

    with patch("app.services.media.audio_extract._resolve_ffmpeg", return_value=None):
        result = extract_audio_for_whisper(input_file, output_file, ffmpeg_path=None)

    assert result == input_file


def test_extract_runs_ffmpeg_with_expected_args(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake")
    output_file = tmp_path / "out.mp3"
    output_file.write_bytes(b"mp3")

    mock_run = MagicMock()
    with patch("app.services.media.audio_extract._resolve_ffmpeg", return_value="/usr/bin/ffmpeg"):
        with patch("app.services.media.audio_extract.subprocess.run", mock_run):
            result = extract_audio_for_whisper(input_file, output_file)

    assert result == output_file
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "/usr/bin/ffmpeg"
    assert "-ar" in cmd and "16000" in cmd
    assert "-ac" in cmd and "1" in cmd


def test_extract_falls_back_on_ffmpeg_failure(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake")
    output_file = tmp_path / "out.mp3"

    with patch("app.services.media.audio_extract._resolve_ffmpeg", return_value="/usr/bin/ffmpeg"):
        with patch(
            "app.services.media.audio_extract.subprocess.run",
            side_effect=OSError("ffmpeg failed"),
        ):
            result = extract_audio_for_whisper(input_file, output_file)

    assert result == input_file
