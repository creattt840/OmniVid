"""转录文本质量检测：拦截纯音乐/幻听/无效自动字幕。"""

import re

# Whisper 常见幻听：音乐标签、曲名括号、重复短句
_MUSIC_LABEL_RE = re.compile(
    r"(\[.*?\]|"
    r"музык|music|pomp and circumstance|"
    r"заставка|instrumental|"
    r"♪|背景音乐|纯音乐)",
    re.IGNORECASE,
)

_MIN_SPEECH_CHARS = 50
_MIN_SPEECH_RATIO = 0.05  # 有效文本字符数 / 视频秒数


def _speech_char_count(segments: list) -> int:
    return sum(len(s.get("text", "").strip()) for s in segments)


def _speech_duration(segments: list) -> float:
    total = 0.0
    for s in segments:
        text = s.get("text", "").strip()
        if text:
            total += max(0.0, float(s.get("end", 0)) - float(s.get("start", 0)))
    return total


def is_low_quality_transcript(segments: list, duration: int = 0) -> tuple[bool, str]:
    """
    判断转录是否不足以支撑 AI 分析。
    返回 (is_low_quality, reason)。
    """
    if not segments:
        return True, "未检测到可转写的语音内容"

    texts = [s.get("text", "").strip() for s in segments if s.get("text", "").strip()]
    if not texts:
        return True, "未检测到可转写的语音内容"

    char_count = _speech_char_count(segments)
    if char_count < _MIN_SPEECH_CHARS:
        return True, f"有效转录文本过短（{char_count} 字），可能为纯音乐或默剧视频"

    music_like = sum(1 for t in texts if _MUSIC_LABEL_RE.search(t))
    if music_like == len(texts):
        return True, "转录内容均为音乐/音效标签，未检测到人声对白"

    if len(texts) >= 3:
        unique = {t.lower() for t in texts}
        if len(unique) <= 2 and music_like >= len(texts) - 1:
            return True, "转录内容为重复的音乐标签，无法生成可靠分析"

    if duration and duration > 0:
        ratio = char_count / duration
        if ratio < _MIN_SPEECH_RATIO:
            return True, "人声内容占比过低，可能为纯背景音乐或游戏音效视频"

    speech_dur = _speech_duration(segments)
    if duration and duration > 60 and speech_dur < duration * 0.03:
        return True, "检测到的语音时长过短，无法生成可靠分析"

    return False, ""


def assert_transcript_quality(segments: list, duration: int = 0) -> None:
    bad, reason = is_low_quality_transcript(segments, duration)
    if bad:
        raise ValueError(
            f"未检测到足够的人声内容，无法生成可靠分析（{reason}）。"
            "此类视频可能为纯音乐、默剧或仅含游戏音效。"
        )
