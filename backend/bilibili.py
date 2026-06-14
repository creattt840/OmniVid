"""B 站视频解析与下载模块 — 基于公开 API，绕过 yt-dlp 412 反爬"""

import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx

logger = logging.getLogger("bilibili")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://www.bilibili.com",
}

QN_LABELS = {6: "240P", 16: "360P", 32: "480P", 64: "720P", 74: "720P60",
             80: "1080P", 112: "1080P+", 116: "1080P60", 120: "4K"}
QN_HEIGHT = {6: 240, 16: 360, 32: 480, 64: 720, 74: 720,
             80: 1080, 112: 1080, 116: 1080, 120: 2160, 125: 1080, 126: 1080, 127: 4320}

_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_BVID_PATTERN = re.compile(r"(BV[a-zA-Z0-9]+)", re.IGNORECASE)
_AVID_PATTERN = re.compile(r"[/?&]av(\d+)", re.IGNORECASE)


def is_bilibili_url(url: str) -> bool:
    domains = ["bilibili.com", "b23.tv", "bili2233.cn"]
    try:
        host = urlparse(url).netloc.lower()
        return any(d in host for d in domains)
    except Exception:
        return False


class BilibiliParser:
    VIEW_API = "https://api.bilibili.com/x/web-interface/view"
    PLAYURL_API = "https://api.bilibili.com/x/player/playurl"
    DM_VIEW_API = "https://api.bilibili.com/x/v2/dm/view"

    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = 15.0
        self.max_retries = 3

    def parse(self, url: str) -> dict:
        share_url = self._extract_url(url)
        resolved_url = self._resolve_redirect(share_url)
        bvid, aid, page = self._parse_video_id(resolved_url)

        view_data = self._fetch_view(bvid=bvid, aid=aid)
        cid = self._resolve_cid(view_data, page)
        aid = view_data["aid"]
        formats = self._fetch_formats(aid, cid, bvid)
        subtitle_langs = self._fetch_subtitle_langs(aid, cid, bvid)

        stat = view_data.get("stat") or {}
        owner = view_data.get("owner") or {}
        duration = view_data.get("duration") or 0
        pic = view_data.get("pic") or ""
        if pic.startswith("//"):
            pic = "https:" + pic

        upload_date = ""
        pubdate = view_data.get("pubdate")
        if pubdate:
            from datetime import datetime
            upload_date = datetime.fromtimestamp(pubdate).strftime("%Y%m%d")

        return {
            "id": bvid or str(aid),
            "title": view_data.get("title") or "未知标题",
            "thumbnail": pic,
            "duration": duration,
            "duration_string": self._fmt_duration(duration),
            "uploader": owner.get("name", "B站用户"),
            "platform": "哔哩哔哩",
            "view_count": stat.get("view"),
            "upload_date": upload_date,
            "description": (view_data.get("desc") or view_data.get("title") or "")[:200],
            "formats": formats,
            "subtitles": subtitle_langs.get("manual", []),
            "automatic_captions": subtitle_langs.get("auto", []),
        }

    def download(self, url: str, format_id: str = "bili_64") -> dict:
        share_url = self._extract_url(url)
        resolved_url = self._resolve_redirect(share_url)
        bvid, aid, page = self._parse_video_id(resolved_url)

        view_data = self._fetch_view(bvid=bvid, aid=aid)
        cid = self._resolve_cid(view_data, page)
        aid = view_data["aid"]
        qn = self._parse_format_qn(format_id)

        play_data = self._fetch_playurl(aid, cid, qn, bvid)
        media_url = self._get_media_url(play_data)
        if not media_url:
            raise ValueError("未找到可下载的播放地址")

        title = view_data.get("title") or f"bilibili_{bvid or aid}"
        safe_title = re.sub(r'[\\/*?:"<>|\n\r\t]', "_", title).strip("_. ")[:60]
        safe_title = re.sub(r"_+", "_", safe_title) or f"bilibili_{bvid or aid}"

        ext = "flv" if ".flv" in media_url.split("?")[0] else "mp4"
        filename = f"{safe_title}.{ext}"
        filepath = self.download_dir / filename
        referer = f"https://www.bilibili.com/video/{bvid}" if bvid else "https://www.bilibili.com/"
        self._download_file(media_url, filepath, referer)

        return {"filepath": str(filepath), "filename": filename, "title": title, "ext": ext}

    def get_direct_url(self, url: str, format_id: str = "bili_64") -> dict:
        share_url = self._extract_url(url)
        resolved_url = self._resolve_redirect(share_url)
        bvid, aid, page = self._parse_video_id(resolved_url)

        view_data = self._fetch_view(bvid=bvid, aid=aid)
        cid = self._resolve_cid(view_data, page)
        aid = view_data["aid"]
        qn = self._parse_format_qn(format_id)

        play_data = self._fetch_playurl(aid, cid, qn, bvid)
        media_url = self._get_media_url(play_data)
        if not media_url:
            raise ValueError("未找到可下载的播放地址")

        durl = play_data.get("durl") or []
        return {
            "direct_url": media_url,
            "ext": "flv" if ".flv" in media_url.split("?")[0] else "mp4",
            "filesize": durl[0].get("size") if durl else None,
            "title": view_data.get("title", "video"),
        }

    def _headers(self, referer: str) -> dict:
        return {**DEFAULT_HEADERS, "Referer": referer}

    def _extract_url(self, text: str) -> str:
        match = _URL_PATTERN.search(text)
        if not match:
            raise ValueError("未找到有效的 B 站链接")
        return match.group(0).strip().strip('"').strip("'").rstrip(").,;!?")

    def _resolve_redirect(self, url: str) -> str:
        try:
            with httpx.Client(follow_redirects=True, timeout=self.timeout) as client:
                return str(client.get(url, headers=DEFAULT_HEADERS).url)
        except Exception:
            return url

    def _parse_video_id(self, url: str) -> tuple[Optional[str], Optional[int], int]:
        bvid_match = _BVID_PATTERN.search(url)
        bvid = bvid_match.group(1) if bvid_match else None
        aid_match = _AVID_PATTERN.search(url)
        aid = int(aid_match.group(1)) if aid_match else None

        if not bvid and not aid:
            raise ValueError("无法从链接中识别 BV 号或 av 号")

        page = 1
        parsed = urlparse(url)
        if parsed.query:
            p_val = parse_qs(parsed.query).get("p", ["1"])[0]
            try:
                page = max(1, int(p_val))
            except ValueError:
                page = 1
        return bvid, aid, page

    def _fetch_view(self, bvid: Optional[str] = None, aid: Optional[int] = None) -> dict:
        if bvid:
            params, referer = {"bvid": bvid}, f"https://www.bilibili.com/video/{bvid}"
        elif aid:
            params, referer = {"aid": aid}, f"https://www.bilibili.com/video/av{aid}"
        else:
            raise ValueError("缺少 bvid 或 aid")

        resp = httpx.get(self.VIEW_API, params=params, headers=self._headers(referer), timeout=self.timeout)
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 0:
            raise ValueError(body.get("message") or "B 站 API 返回错误")
        data = body.get("data")
        if not data:
            raise ValueError("无法获取视频信息，视频可能不存在或已被删除")
        return data

    @staticmethod
    def _resolve_cid(view_data: dict, page: int) -> int:
        pages = view_data.get("pages") or []
        if pages:
            cid = pages[min(page - 1, len(pages) - 1)].get("cid")
            if cid:
                return cid
        cid = view_data.get("cid")
        if not cid:
            raise ValueError("无法获取视频 cid")
        return cid

    def _fetch_playurl(self, aid: int, cid: int, qn: int, bvid: Optional[str] = None) -> dict:
        referer = f"https://www.bilibili.com/video/{bvid}" if bvid else "https://www.bilibili.com/"
        resp = httpx.get(
            self.PLAYURL_API,
            params={"avid": aid, "cid": cid, "qn": qn, "fnval": 1, "fnver": 0, "fourk": 1},
            headers=self._headers(referer),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 0:
            raise ValueError(body.get("message") or "获取播放地址失败")
        data = body.get("data")
        if not data:
            raise ValueError("播放地址为空")
        return data

    def _fetch_formats(self, aid: int, cid: int, bvid: Optional[str]) -> list:
        base = self._fetch_playurl(aid, cid, 80, bvid)
        qualities = base.get("accept_quality") or [base.get("quality", 64)]
        descriptions = base.get("accept_description") or []
        qn_to_desc = {qn: descriptions[i] for i, qn in enumerate(qualities) if i < len(descriptions)}

        formats, seen_qn = [], set()
        for qn in qualities:
            if qn in seen_qn:
                continue
            seen_qn.add(qn)
            try:
                play_data = self._fetch_playurl(aid, cid, qn, bvid)
            except Exception:
                continue
            media_url = self._get_media_url(play_data)
            if not media_url:
                continue

            durl = play_data.get("durl") or []
            filesize = durl[0].get("size") if durl else None
            height = QN_HEIGHT.get(qn, 720)
            label_text = qn_to_desc.get(qn) or QN_LABELS.get(qn, f"{height}P")
            ext = "flv" if ".flv" in media_url.split("?")[0] else "mp4"

            formats.append({
                "format_id": f"bili_{qn}",
                "ext": ext,
                "resolution": f"?x{height}",
                "height": height,
                "filesize": filesize,
                "filesize_approx": filesize,
                "vcodec": "avc",
                "acodec": "aac",
                "has_audio": True,
                "label": f"{label_text} {ext.upper()} ({self._format_filesize(filesize)})",
                "_direct_url": media_url,
            })

        formats.sort(key=lambda x: x["height"], reverse=True)
        return formats[:15]

    def _fetch_subtitle_langs(self, aid: int, cid: int, bvid: Optional[str]) -> dict:
        entries = self.fetch_subtitle_entries(aid, cid, bvid)
        manual, auto = [], []
        for e in entries:
            (auto if e.get("is_auto") else manual).append(e["lang"])
        return {"manual": manual, "auto": auto}

    def fetch_subtitle_entries(self, aid: int, cid: int, bvid: Optional[str]) -> list:
        """返回字幕列表 [{lang, url, is_auto}, ...]"""
        entries = []
        try:
            referer = f"https://www.bilibili.com/video/{bvid}" if bvid else "https://www.bilibili.com/"
            resp = httpx.get(
                self.DM_VIEW_API,
                params={"aid": aid, "oid": cid, "type": 1},
                headers=self._headers(referer),
                timeout=self.timeout,
            )
            sub_list = resp.json().get("data", {}).get("subtitle", {}).get("subtitles", [])
            for s in sub_list:
                lang = s.get("lan", "")
                sub_url = s.get("subtitle_url", "")
                if sub_url.startswith("//"):
                    sub_url = "https:" + sub_url
                if sub_url:
                    entries.append({
                        "lang": lang,
                        "url": sub_url,
                        "is_auto": lang.startswith("ai-"),
                    })
        except Exception:
            pass
        return entries

    @staticmethod
    def _get_media_url(play_data: dict) -> Optional[str]:
        durl = play_data.get("durl") or []
        if durl:
            return durl[0].get("url")
        dash = play_data.get("dash") or {}
        videos = dash.get("video") or []
        if videos:
            return videos[0].get("baseUrl") or videos[0].get("base_url")
        return None

    @staticmethod
    def _parse_format_qn(format_id: str) -> int:
        if format_id.startswith("bili_"):
            try:
                return int(format_id[5:])
            except ValueError:
                pass
        try:
            return int(format_id)
        except ValueError:
            return 64

    @staticmethod
    def _format_filesize(size: Optional[int]) -> str:
        if not size:
            return "未知大小"
        if size < 1024 * 1024:
            return f"{size / 1024:.0f}KB"
        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f}MB"
        return f"{size / (1024 * 1024 * 1024):.2f}GB"

    @staticmethod
    def _fmt_duration(seconds: Optional[int]) -> str:
        if not seconds:
            return "00:00"
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _download_file(self, url: str, filepath: Path, referer: str, chunk_size: int = 256 * 1024):
        headers = self._headers(referer)
        for attempt in range(self.max_retries):
            try:
                with httpx.stream("GET", url, headers=headers, timeout=60.0, follow_redirects=True) as resp:
                    resp.raise_for_status()
                    temp_path = filepath.with_suffix(filepath.suffix + ".part")
                    with temp_path.open("wb") as f:
                        for chunk in resp.iter_bytes(chunk_size):
                            f.write(chunk)
                    temp_path.replace(filepath)
                return
            except Exception as e:
                if attempt == self.max_retries - 1:
                    filepath.unlink(missing_ok=True)
                    raise ValueError(f"下载失败: {e}") from e
                logger.warning("B站下载重试 %d/%d: %s", attempt + 1, self.max_retries, e)
