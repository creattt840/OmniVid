"""yt-dlp 公共配置：代理、超时、YouTube 多客户端回退"""

from __future__ import annotations

from app.core.config import get_settings
import re
from typing import Any, Iterator, Optional

import yt_dlp

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
YOUTUBE_HOST = re.compile(r"(youtube\.com|youtu\.be)", re.I)

# 网络不稳时依次尝试的 YouTube 客户端
YOUTUBE_PLAYER_CLIENTS: list[Optional[list[str]]] = [
    None,
    ["android", "web"],
    ["ios", "web"],
    ["tv_embedded", "web"],
    ["mweb", "web"],
]


def is_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_HOST.search(url or ""))


def build_ydl_opts(**overrides: Any) -> dict:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 3,
    }
    proxy = get_settings().ytdlp_proxy
    if proxy:
        opts["proxy"] = proxy
    opts.update(overrides)
    return opts


def iter_ytdlp_strategies(url: str) -> Iterator[dict]:
    yield build_ydl_opts()
    if not is_youtube_url(url):
        return
    for clients in YOUTUBE_PLAYER_CLIENTS[1:]:
        yield build_ydl_opts(extractor_args={"youtube": {"player_client": clients}})


def extract_info(url: str, download: bool = False, **extra_opts: Any) -> dict:
    last_err: Optional[Exception] = None
    for base in iter_ytdlp_strategies(url):
        opts = {**base, **extra_opts}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=download)
            if info:
                return info
            raise ValueError("无法解析该链接")
        except Exception as exc:
            last_err = exc
    assert last_err is not None
    raise last_err


def download(url: str, **extra_opts: Any) -> None:
    last_err: Optional[Exception] = None
    for base in iter_ytdlp_strategies(url):
        opts = {**base, **extra_opts}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            return
        except Exception as exc:
            last_err = exc
    assert last_err is not None
    raise last_err


def download_from_info(url: str, info: dict, **extra_opts: Any) -> dict:
    """复用已缓存的 extract_info 结果下载，避免重复拉取元数据。"""
    last_err: Optional[Exception] = None
    for base in iter_ytdlp_strategies(url):
        opts = {**base, **extra_opts}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.process_ie_result(info.copy(), download=True)
            return info
        except Exception as exc:
            last_err = exc
    assert last_err is not None
    raise last_err


def format_ytdlp_error(exc: Exception, *, url: str = "") -> str:
    """将 yt-dlp 原始异常转为用户可读提示"""
    msg = ANSI_ESCAPE.sub("", str(exc)).strip()
    msg = re.sub(r"^ERROR:\s*", "", msg, flags=re.I)

    network_markers = (
        "SSL",
        "UNEXPECTED_EOF",
        "timed out",
        "Timeout",
        "Connection",
        "Unable to download API page",
        "Network is unreachable",
        "getaddrinfo failed",
    )
    if is_youtube_url(url) and any(m.lower() in msg.lower() for m in network_markers):
        proxy_hint = get_settings().ytdlp_proxy
        base = (
            "无法稳定连接 YouTube（网络超时或 SSL 中断）。"
            "请确认本机可访问 YouTube，或配置代理后重试。"
        )
        if proxy_hint:
            return f"{base} 当前已配置代理：{proxy_hint}"
        return (
            f"{base} 可在 backend/.env 中设置 YTDLP_PROXY=http://127.0.0.1:7890 "
            f"（按你的代理端口修改），然后重启后端。"
        )

    if len(msg) > 280:
        msg = msg[:277] + "..."
    return msg
