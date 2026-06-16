"""转录质量门控单元测试。"""
import pytest

from app.services.ai.transcript_quality import assert_transcript_quality, is_low_quality_transcript


def test_empty_segments_rejected():
    bad, reason = is_low_quality_transcript([], duration=120)
    assert bad is True
    with pytest.raises(ValueError, match="未检测到足够的人声内容"):
        assert_transcript_quality([], duration=120)


def test_music_only_whisper_hallucination_rejected():
    segments = [
        {"start": 0.0, "end": 10.0, "text": "МУЗЫКАЛЬНАЯ ЗАСТАВКА"},
        {"start": 30.0, "end": 40.0, "text": "МУЗЫКАЛЬНАЯ ЗАСТАВКА"},
    ]
    bad, _ = is_low_quality_transcript(segments, duration=274)
    assert bad is True
    with pytest.raises(ValueError, match="音乐"):
        assert_transcript_quality(segments, duration=274)


def test_pomp_and_circumstance_labels_rejected():
    segments = [
        {"start": 0.0, "end": 5.0, "text": '["Pomp and Circumstance"]'},
        {"start": 30.0, "end": 35.0, "text": '["Pomp and Circumstance"]'},
    ]
    with pytest.raises(ValueError):
        assert_transcript_quality(segments, duration=146)


def test_short_auto_cc_subtitle_rejected():
    segments = [
        {"start": 37.0, "end": 42.0, "text": "可可妈妈说快点进来"},
        {"start": 50.0, "end": 51.0, "text": "♪ 聚集农村 ♪"},
    ]
    with pytest.raises(ValueError, match="过短"):
        assert_transcript_quality(segments, duration=363)


def test_normal_speech_passes():
    segments = [
        {"start": 0.0, "end": 5.0, "text": "大家好，今天我们来讲解 Python 编程的基础知识。"},
        {"start": 5.0, "end": 12.0, "text": "首先我们需要了解变量和数据类型，这是写代码的第一步。"},
        {"start": 12.0, "end": 20.0, "text": "接下来会演示如何在项目中安装依赖并运行示例程序。"},
    ]
    bad, reason = is_low_quality_transcript(segments, duration=600)
    assert bad is False, reason
    assert_transcript_quality(segments, duration=600)
