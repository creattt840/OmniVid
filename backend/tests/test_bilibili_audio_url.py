"""B站 DASH 音频 URL 选择单元测试。"""
from app.services.video.bilibili import BilibiliParser


def test_get_audio_url_prefers_dash_audio():
    play_data = {
        "dash": {
            "audio": [
                {"bandwidth": 128000, "baseUrl": "https://example.com/audio_hi.m4a"},
                {"bandwidth": 64000, "baseUrl": "https://example.com/audio_lo.m4a"},
            ],
            "video": [{"baseUrl": "https://example.com/video.mp4"}],
        }
    }
    url, needs_extract = BilibiliParser._get_audio_url(play_data)
    assert url == "https://example.com/audio_lo.m4a"
    assert needs_extract is False


def test_get_audio_url_falls_back_to_durl_with_extract():
    play_data = {
        "durl": [{"url": "https://example.com/progressive.flv"}],
    }
    url, needs_extract = BilibiliParser._get_audio_url(play_data)
    assert url == "https://example.com/progressive.flv"
    assert needs_extract is True


def test_get_audio_url_falls_back_to_dash_video_with_extract():
    play_data = {
        "dash": {
            "video": [{"baseUrl": "https://example.com/video_only.mp4"}],
        }
    }
    url, needs_extract = BilibiliParser._get_audio_url(play_data)
    assert url == "https://example.com/video_only.mp4"
    assert needs_extract is True


def test_get_audio_url_returns_none_when_empty():
    url, needs_extract = BilibiliParser._get_audio_url({})
    assert url is None
    assert needs_extract is False
