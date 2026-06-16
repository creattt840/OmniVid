"""URL 解析元数据短时缓存，避免 parse → analyze 重复拉取平台 API / yt-dlp。"""

import time
from typing import Any, Optional

TTL_SECONDS = 600

_store: dict[str, tuple[float, dict[str, Any]]] = {}


def normalize_url(url: str) -> str:
    return url.strip()


def _get(key: str) -> Optional[dict[str, Any]]:
    entry = _store.get(normalize_url(key))
    if not entry:
        return None
    ts, data = entry
    if time.time() - ts > TTL_SECONDS:
        _store.pop(normalize_url(key), None)
        return None
    return data


def _put(key: str, data: dict[str, Any]) -> None:
    _store[normalize_url(key)] = (time.time(), data)


def put_bilibili(
    url: str,
    *,
    view_data: dict,
    cid: int,
    bvid: Optional[str],
    aid: int,
    page: int,
) -> None:
    _put(
        url,
        {
            "type": "bilibili",
            "view_data": view_data,
            "cid": cid,
            "bvid": bvid,
            "aid": aid,
            "page": page,
        },
    )


def get_bilibili(url: str) -> Optional[dict[str, Any]]:
    data = _get(url)
    if data and data.get("type") == "bilibili":
        return data
    return None


def put_douyin(url: str, *, item_info: dict, video_id: str) -> None:
    _put(url, {"type": "douyin", "item_info": item_info, "video_id": video_id})


def get_douyin(url: str) -> Optional[dict[str, Any]]:
    data = _get(url)
    if data and data.get("type") == "douyin":
        return data
    return None


def put_ytdlp_info(url: str, info: dict) -> None:
    _put(url, {"type": "ytdlp", "info": info})


def get_ytdlp_info(url: str) -> Optional[dict]:
    data = _get(url)
    if data and data.get("type") == "ytdlp":
        return data.get("info")
    return None
