"""视频链接提交前校验（拦截明显非视频 URL）"""

import re
from urllib.parse import urlparse

from app.services.video.bilibili import is_bilibili_url
from app.services.video.douyin import is_douyin_url
from app.services.video.ytdlp_utils import is_youtube_url

_VIDEO_HOST_KEYWORDS = (
    "tiktok.com",
    "vimeo.com",
    "twitch.tv",
    "dailymotion.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "facebook.com",
    "fb.watch",
    "youku.com",
    "iqiyi.com",
    "v.qq.com",
    "acfun.cn",
    "ixigua.com",
    "weibo.com",
    "xiaohongshu.com",
    "reddit.com",
    "nicovideo.jp",
    "streamable.com",
    "rumble.com",
    "kuaishou.com",
)

_VIDEO_PATH_PATTERNS = (
    re.compile(r"/video/", re.I),
    re.compile(r"/watch\b", re.I),
    re.compile(r"[?&]v=", re.I),
    re.compile(r"/shorts/", re.I),
    re.compile(r"/bv[a-z0-9]{10}", re.I),
    re.compile(r"/av\d+", re.I),
)


class VideoUrlValidationError(ValueError):
    pass


def _normalize_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        raise VideoUrlValidationError("请输入视频链接")
    if not re.match(r"^https?://", u, re.I):
        u = f"https://{u}"
    return u


def _host_matches(hostname: str) -> bool:
    host = (hostname or "").lower()
    if is_bilibili_url(f"https://{host}/"):
        return True
    if is_douyin_url(f"https://{host}/"):
        return True
    if is_youtube_url(f"https://{host}/"):
        return True
    return any(k in host for k in _VIDEO_HOST_KEYWORDS)


def _path_matches(pathname: str, search: str) -> bool:
    full = f"{pathname or ''}{search or ''}"
    return any(p.search(full) or p.search(pathname or "") for p in _VIDEO_PATH_PATTERNS)


def validate_video_url(url: str) -> str:
    """校验并返回规范化 URL；无效时抛出 VideoUrlValidationError。"""
    normalized = _normalize_url(url)
    try:
        parsed = urlparse(normalized)
    except Exception as exc:
        raise VideoUrlValidationError("请输入有效的 http/https 链接") from exc

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise VideoUrlValidationError("请输入有效的 http/https 链接")

    if _host_matches(parsed.hostname or "") or _path_matches(parsed.path, parsed.query):
        return normalized

    raise VideoUrlValidationError(
        "无法识别为视频链接，请输入 B站、YouTube、抖音、TikTok 等平台的视频页面地址"
    )
