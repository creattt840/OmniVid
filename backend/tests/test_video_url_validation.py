"""视频链接校验测试。"""
import pytest

from app.services.video.url_validation import VideoUrlValidationError, validate_video_url


def test_rejects_non_video_site():
    with pytest.raises(VideoUrlValidationError, match="无法识别为视频链接"):
        validate_video_url("https://bibigpt.co/en")


def test_rejects_plain_homepage():
    with pytest.raises(VideoUrlValidationError):
        validate_video_url("https://www.google.com")


def test_accepts_bilibili():
    url = validate_video_url("https://www.bilibili.com/video/BV1GJ411x7h7")
    assert "bilibili.com" in url


def test_accepts_youtube():
    url = validate_video_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert "youtube.com" in url


def test_accepts_douyin_share():
    url = validate_video_url("https://v.douyin.com/abc123/")
    assert "douyin.com" in url


def test_normalizes_missing_scheme():
    url = validate_video_url("www.bilibili.com/video/BV1GJ411x7h7")
    assert url.startswith("https://")
