"""Generate frontend/src/data/demo-showcase.json from a live analysis run."""
import json
import re
import sys
import uuid
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
VIDEO_URL = "https://www.bilibili.com/video/BV12LR1B3EUt"
OUT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "data" / "demo-showcase.json"


def parse_sse_lines(text: str):
    for line in text.splitlines():
        if line.startswith("data: "):
            yield json.loads(line[6:])


def register_and_login(client: httpx.Client) -> str:
    email = f"demo-gen-{uuid.uuid4().hex[:8]}@example.com"
    password = "demo123456"
    client.post("/api/auth/register", json={"email": email, "password": password})
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    data = res.json()
    if not data.get("success"):
        raise RuntimeError(f"login failed: {data}")
    return data["data"]["token"]


def main():
    with httpx.Client(base_url=BASE, timeout=600.0) as client:
        health = client.get("/api/health")
        if health.status_code != 200:
            raise RuntimeError(f"backend unhealthy: {health.status_code}")

        parse_res = client.post("/api/parse", json={"url": VIDEO_URL})
        parse_data = parse_res.json()
        if not parse_data.get("success"):
            raise RuntimeError(f"parse failed: {parse_data}")

        video = parse_data["data"]
        token = register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        analyze_res = client.post("/api/analyze", json={"url": VIDEO_URL}, headers=headers)
        analyze_data = analyze_res.json()
        if not analyze_data.get("success"):
            raise RuntimeError(f"analyze failed: {analyze_data}")

        session_id = analyze_data["data"]["session_id"]
        meta = analyze_data["data"]

        segments = []
        summary = {}
        mindmap = ""
        article = ""

        with client.stream("GET", f"/api/analyze/{session_id}/stream", timeout=600.0) as stream:
            buffer = ""
            for chunk in stream.iter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    part, buffer = buffer.split("\n\n", 1)
                    for event in parse_sse_lines(part):
                        et = event.get("type")
                        if et == "transcript":
                            segments = event.get("segments") or []
                        elif et == "summary_done":
                            summary = {
                                "summary": event.get("summary", ""),
                                "highlights": event.get("highlights") or [],
                                "chapters": event.get("chapters") or [],
                                "terms": event.get("terms") or [],
                            }
                        elif et == "mindmap":
                            mindmap = event.get("content") or ""
                        elif et == "error":
                            raise RuntimeError(event.get("message", "stream error"))

        with client.stream("GET", f"/api/analyze/{session_id}/rewrite", headers=headers, timeout=600.0) as stream:
            buffer = ""
            for chunk in stream.iter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    part, buffer = buffer.split("\n\n", 1)
                    for event in parse_sse_lines(part):
                        et = event.get("type")
                        if et == "rewrite_chunk":
                            article += event.get("content") or ""
                        elif et == "rewrite_done":
                            article = event.get("content") or article
                        elif et == "error":
                            raise RuntimeError(event.get("message", "rewrite error"))

        payload = {
            "url": VIDEO_URL,
            "title": meta.get("title") or video.get("title"),
            "platform": meta.get("platform") or video.get("platform"),
            "thumbnail": video.get("thumbnail") or "",
            "duration_string": video.get("duration_string") or "",
            "video": {
                "title": video.get("title"),
                "platform": video.get("platform"),
                "thumbnail": video.get("thumbnail"),
                "duration_string": video.get("duration_string"),
                "formats": [],
            },
            "summary": summary,
            "mindmap": mindmap,
            "segments": segments,
            "article": article,
            "transcriptSource": meta.get("transcript_source") or "subtitle",
        }

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Written {OUT}")
        print(f"segments={len(segments)}, summary_len={len(summary.get('summary', ''))}, article_len={len(article)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
