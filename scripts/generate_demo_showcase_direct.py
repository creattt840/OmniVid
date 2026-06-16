"""Generate demo-showcases.json entries by calling backend services directly."""
import argparse
import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.container import get_bilibili_parser, get_video_analyzer  # noqa: E402
from app.services.video.bilibili import is_bilibili_url  # noqa: E402
from app.services.video.douyin import is_douyin_url  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "data" / "demo-showcases.json"


def slug_from_url(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]+)", url)
        return f"youtube-{m.group(1).lstrip('-')}"
    m = re.search(r"BV[A-Za-z0-9]+", url)
    return m.group(0).lower() if m else "demo"


def platform_label(platform: str, url: str) -> str:
    if is_bilibili_url(url):
        return "B站"
    if "youtube" in url or "youtu.be" in url:
        return "YouTube"
    if is_douyin_url(url):
        return "抖音"
    return platform or "视频"


def parse_sse_line(line: str):
    if line.startswith("data: "):
        return json.loads(line[6:])
    return None


def build_demo_payload(url: str, description: str = "") -> dict:
    if is_bilibili_url(url):
        video = get_bilibili_parser().parse(url)
    else:
        from app.services.container import get_downloader
        video = get_downloader().parse_video(url)

    analyzer = get_video_analyzer()
    if not analyzer.is_ai_available():
        raise RuntimeError("DEEPSEEK_API_KEY not configured")

    print(f"Preparing transcript for {url}...")
    session = analyzer.prepare_transcript(url)
    print(f"  source={session.transcript_source}, segments={len(session.segments)}")

    summary = {}
    mindmap = ""
    for chunk in analyzer.stream_summary(session.session_id):
        for line in chunk.strip().split("\n"):
            event = parse_sse_line(line)
            if not event:
                continue
            et = event.get("type")
            if et == "summary_done":
                summary = {
                    "summary": event.get("summary", ""),
                    "highlights": event.get("highlights") or [],
                    "chapters": event.get("chapters") or [],
                    "terms": event.get("terms") or [],
                }
            elif et == "mindmap":
                mindmap = event.get("content") or ""
            elif et == "error":
                raise RuntimeError(event.get("message", "summary error"))

    article = ""
    for chunk in analyzer.stream_rewrite(session.session_id):
        for line in chunk.strip().split("\n"):
            event = parse_sse_line(line)
            if not event:
                continue
            et = event.get("type")
            if et == "rewrite_chunk":
                article += event.get("content") or ""
            elif et == "rewrite_done":
                article = event.get("content") or article
            elif et == "error":
                raise RuntimeError(event.get("message", "rewrite error"))

    title = session.title or video.get("title") or ""
    plat = session.platform or video.get("platform") or ""
    prefix = platform_label(plat, url)
    short_title = title if len(title) <= 28 else title[:28] + "…"

    return {
        "id": slug_from_url(url),
        "label": f"{prefix}：{short_title}",
        "description": description or summary.get("summary", "")[:80] + ("…" if len(summary.get("summary", "")) > 80 else ""),
        "url": url.split("?")[0] if "bilibili" in url else url,
        "title": title,
        "platform": plat,
        "thumbnail": video.get("thumbnail") or "",
        "duration_string": video.get("duration_string") or "",
        "video": {
            "title": video.get("title"),
            "platform": plat,
            "thumbnail": video.get("thumbnail"),
            "duration_string": video.get("duration_string"),
            "formats": [],
        },
        "summary": summary,
        "mindmap": mindmap,
        "segments": session.segments,
        "article": article,
        "transcriptSource": session.transcript_source,
    }


def load_store() -> dict:
    if OUT.exists():
        data = json.loads(OUT.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"demos": data}
        return data
    return {"demos": []}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Video URL to generate")
    parser.add_argument("--description", default="", help="Switcher card subtitle")
    parser.add_argument("--replace-all", action="store_true", help="Replace entire file with single demo")
    args = parser.parse_args()

    payload = build_demo_payload(args.url.strip(), args.description)

    if args.replace_all:
        store = {"demos": [payload]}
    else:
        store = load_store()
        demos = store.get("demos", [])
        demos = [d for d in demos if d.get("id") != payload["id"]]
        demos.append(payload)
        store["demos"] = demos

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {OUT} ({len(store['demos'])} demos)")


if __name__ == "__main__":
    main()
