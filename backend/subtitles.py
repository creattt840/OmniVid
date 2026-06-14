"""统一字幕拉取：B站 API + yt-dlp 字幕下载，解析为带时间戳 segments"""

import json
import logging
import re
import shutil
import uuid
from pathlib import Path
from typing import Optional

import httpx
import yt_dlp

from bilibili import BilibiliParser, is_bilibili_url
from douyin import is_douyin_url

logger = logging.getLogger("subtitles")

Segment = dict  # {"start": float, "end": float, "text": str}

PREFERRED_LANGS = ["zh-Hans", "zh-CN", "zh", "zh-Hant", "en", "ja", "ko"]


def _format_timestamp(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _pick_lang(available: list[str]) -> Optional[str]:
    for lang in PREFERRED_LANGS:
        if lang in available:
            return lang
    return available[0] if available else None


def _pick_subtitle_lang(manual: dict, auto: dict) -> tuple[Optional[str], bool]:
    """优先人工字幕，再自动字幕；返回 (lang, is_auto)"""
    manual_langs = list(manual.keys())
    lang = _pick_lang(manual_langs)
    if lang:
        return lang, False
    auto_langs = [k for k in auto.keys() if k not in manual]
    lang = _pick_lang(auto_langs)
    if lang:
        return lang, True
    return None, False


def _parse_vtt(content: str) -> list[Segment]:
    segments = []
    blocks = re.split(r"\n\n+", content.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        time_line = None
        for line in lines:
            if "-->" in line:
                time_line = line
                break
        if not time_line:
            continue
        match = re.match(
            r"(\d{1,2}:?\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{1,2}:?\d{2}:\d{2}[.,]\d{3})",
            time_line,
        )
        if not match:
            continue

        def _to_sec(ts: str) -> float:
            ts = ts.replace(",", ".")
            parts = ts.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            return int(parts[0]) * 60 + float(parts[1])

        start = _to_sec(match.group(1))
        end = _to_sec(match.group(2))
        text_lines = [
            ln for ln in lines
            if ln != time_line and not ln.isdigit() and not ln.startswith("WEBVTT")
        ]
        text = re.sub(r"<[^>]+>", "", " ".join(text_lines)).strip()
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return segments


def _parse_srt(content: str) -> list[Segment]:
    vtt = re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", content)
    return _parse_vtt(vtt)


def _parse_bilibili_json(data: dict) -> list[Segment]:
    segments = []
    for item in data.get("body", []):
        text = (item.get("content") or "").strip()
        if not text:
            continue
        segments.append({
            "start": float(item.get("from", 0)),
            "end": float(item.get("to", 0)),
            "text": text,
        })
    return segments


def _parse_json3(content: str) -> list[Segment]:
    """YouTube json3 字幕格式"""
    segments = []
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return segments
    for event in data.get("events") or []:
        if "segs" not in event:
            continue
        text = "".join(s.get("utf8", "") for s in event["segs"]).strip()
        if not text or text == "\n":
            continue
        start_ms = event.get("tStartMs", 0)
        dur_ms = event.get("dDurationMs", 0)
        segments.append({
            "start": start_ms / 1000.0,
            "end": (start_ms + dur_ms) / 1000.0,
            "text": text,
        })
    return segments


def _parse_subtitle_content(content: str, ext: str = "") -> list[Segment]:
    content = content.strip()
    if not content:
        return []
    if ext == "json3" or (content.startswith("{") and '"events"' in content):
        segs = _parse_json3(content)
        if segs:
            return segs
    if ext == "json" or (content.startswith("{") and '"body"' in content):
        try:
            return _parse_bilibili_json(json.loads(content))
        except json.JSONDecodeError:
            pass
    if ext in ("srt",) or re.match(r"^\d+\s*\n\d{2}:\d{2}", content):
        return _parse_srt(content)
    return _parse_vtt(content)


class SubtitleFetcher:
    def __init__(self, download_dir: str, bilibili_parser: BilibiliParser):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.bilibili = bilibili_parser

    def fetch_from_url(self, url: str) -> tuple[list[Segment], dict]:
        """
        尝试从字幕获取转录文本。
        返回 (segments, meta)，meta 含 title/duration/platform。
        若无字幕 segments 为空。
        """
        if is_bilibili_url(url):
            return self._fetch_bilibili(url)
        if is_douyin_url(url):
            return [], {}
        return self._fetch_ytdlp(url)

    def _fetch_bilibili(self, url: str) -> tuple[list[Segment], dict]:
        share_url = self.bilibili._extract_url(url)
        resolved = self.bilibili._resolve_redirect(share_url)
        bvid, aid, page = self.bilibili._parse_video_id(resolved)
        view_data = self.bilibili._fetch_view(bvid=bvid, aid=aid)
        cid = self.bilibili._resolve_cid(view_data, page)
        aid = view_data["aid"]
        duration = view_data.get("duration") or 0

        meta = {
            "title": view_data.get("title") or "未知标题",
            "duration": duration,
            "platform": "哔哩哔哩",
        }

        subs = self.bilibili.fetch_subtitle_entries(aid, cid, bvid)
        if not subs:
            return [], meta

        preferred = _pick_lang([s["lang"] for s in subs])
        entry = next((s for s in subs if s["lang"] == preferred), subs[0])
        segments = self._download_and_parse(entry["url"], ext="json")
        return segments, meta

    def _fetch_ytdlp(self, url: str) -> tuple[list[Segment], dict]:
        ydl_opts = {"quiet": True, "no_warnings": True, "noplaylist": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return [], {}

        meta = {
            "title": info.get("title") or "未知标题",
            "duration": info.get("duration") or 0,
            "platform": info.get("extractor", info.get("extractor_key", "Unknown")),
        }

        manual = info.get("subtitles") or {}
        auto = info.get("automatic_captions") or {}
        lang, is_auto = _pick_subtitle_lang(manual, auto)
        if not lang:
            return [], meta

        segments = self._download_subtitles_via_ytdlp(url, lang, is_auto)
        if segments:
            return segments, meta

        sub_list = (auto if is_auto else manual).get(lang) or []
        if not sub_list:
            return [], meta

        for item in sub_list:
            sub_url = item.get("url")
            ext = item.get("ext", "vtt")
            if not sub_url:
                continue
            if "tlang=" in sub_url:
                continue
            segments = self._download_and_parse(sub_url, ext=ext)
            if segments:
                return segments, meta

        return [], meta

    def _download_subtitles_via_ytdlp(self, url: str, lang: str, is_auto: bool) -> list[Segment]:
        work_dir = self.download_dir / f"subs_{uuid.uuid4().hex[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "skip_download": True,
                "outtmpl": str(work_dir / "%(id)s"),
                "subtitlesformat": "vtt",
                "subtitleslangs": [lang],
            }
            if is_auto:
                ydl_opts["writeautomaticsub"] = True
            else:
                ydl_opts["writesubtitles"] = True

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            for f in sorted(work_dir.iterdir()):
                if f.suffix.lower() in (".vtt", ".srt", ".ass"):
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    segs = _parse_subtitle_content(content, ext=f.suffix[1:])
                    if segs:
                        return segs
            return []
        except Exception as e:
            logger.warning("yt-dlp 字幕下载失败: %s", e)
            return []
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _download_and_parse(self, sub_url: str, ext: str = "vtt") -> list[Segment]:
        try:
            if sub_url.startswith("//"):
                sub_url = "https:" + sub_url
            resp = httpx.get(
                sub_url,
                headers={"User-Agent": "Mozilla/5.0", "Referer": sub_url},
                timeout=30,
                follow_redirects=True,
            )
            resp.raise_for_status()
            return _parse_subtitle_content(resp.text, ext=ext)
        except Exception as e:
            logger.warning("字幕下载/解析失败: %s", e)
            return []

    @staticmethod
    def segments_to_text(segments: list[Segment]) -> str:
        lines = []
        for seg in segments:
            ts = _format_timestamp(seg["start"])
            lines.append(f"[{ts}] {seg['text']}")
        return "\n".join(lines)
