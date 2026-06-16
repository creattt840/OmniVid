"""Evaluate AI analysis on low-speech / music-only videos (hallucination baseline)."""
import json
import re
import sys
import traceback
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.container import get_bilibili_parser, get_subtitle_fetcher, get_video_analyzer  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "eval_results"

TEST_VIDEOS = [
    "https://www.bilibili.com/video/BV1vcoNBjELQ",
    "https://www.bilibili.com/video/BV1jM4m1R7zk",
    "https://www.bilibili.com/video/BV1pP4y1R7eT",
]

GROUND_TRUTH = {
    "BV1vcoNBjELQ": {
        "speech_level": "music_only",
        "has_dialogue": False,
        "has_cc_subtitle": False,
        "content_type": "游戏实况/BGM，无清晰对白（验证码相关短视频）",
        "verifiable_facts": [
            "视频为游戏画面剪辑，以背景音乐为主",
            "无连续清晰的人声解说或对白",
            "不应出现具体教程式口播内容摘要",
        ],
    },
    "BV1jM4m1R7zk": {
        "speech_level": "none",
        "has_dialogue": False,
        "has_cc_subtitle": True,
        "content_type": "游戏/短视频类，以画面和音乐为主",
        "verifiable_facts": [
            "以视觉画面和背景音乐为主",
            "无结构化口播讲解",
            "不应编造验证码或登录教程类口播内容",
        ],
    },
    "BV1pP4y1R7eT": {
        "speech_level": "none",
        "has_dialogue": False,
        "has_cc_subtitle": False,
        "content_type": "CSGO 默剧《我很神秘》，游戏音效无对白",
        "verifiable_facts": [
            "CSGO 游戏默剧/搞笑剪辑，标题为《我很神秘》",
            "无人物对白，仅有游戏音效和背景音乐",
            "内容围绕 CSGO 游戏画面与 timing/操作",
            "不应出现演讲、课程、访谈类口播摘要",
        ],
    },
}


def bvid_from_url(url: str) -> str:
    m = re.search(r"BV[A-Za-z0-9]+", url)
    return m.group(0) if m else "unknown"


def parse_sse_line(line: str):
    if line.startswith("data: "):
        return json.loads(line[6:])
    return None


def fetch_metadata(url: str) -> dict:
    parser = get_bilibili_parser()
    fetcher = get_subtitle_fetcher()
    video = parser.parse(url)
    segments, meta = fetcher.fetch_from_url(url)
    bvid = bvid_from_url(url)
    return {
        "bvid": bvid,
        "url": url.split("?")[0],
        "title": meta.get("title") or video.get("title"),
        "duration": meta.get("duration") or video.get("duration"),
        "platform": meta.get("platform") or video.get("platform"),
        "subtitle_segment_count": len(segments),
        "subtitle_preview": [s.get("text", "") for s in segments[:5]],
        "ground_truth": GROUND_TRUTH.get(bvid, {}),
    }


def run_analysis(url: str, suffix: str = "") -> dict:
    bvid = bvid_from_url(url)
    analyzer = get_video_analyzer()
    result = {
        "bvid": bvid,
        "url": url.split("?")[0],
        "ground_truth": GROUND_TRUTH.get(bvid, {}),
        "error": None,
        "transcript_source": None,
        "segment_count": 0,
        "segments": [],
        "transcript_text": "",
        "summary": {},
        "mindmap": "",
        "article": "",
    }

    if not analyzer.is_ai_available():
        result["error"] = "DEEPSEEK_API_KEY not configured"
        return result

    try:
        session = analyzer.prepare_transcript(url)
        result["title"] = session.title
        result["duration"] = session.duration
        result["transcript_source"] = session.transcript_source
        result["segment_count"] = len(session.segments)
        result["segments"] = session.segments
        from app.services.ai.subtitles import SubtitleFetcher

        result["transcript_text"] = SubtitleFetcher.segments_to_text(session.segments)

        for chunk in analyzer.stream_summary(session.session_id):
            for line in chunk.strip().split("\n"):
                event = parse_sse_line(line)
                if not event:
                    continue
                et = event.get("type")
                if et == "summary_done":
                    result["summary"] = {
                        "summary": event.get("summary", ""),
                        "highlights": event.get("highlights") or [],
                        "chapters": event.get("chapters") or [],
                        "terms": event.get("terms") or [],
                    }
                elif et == "mindmap":
                    result["mindmap"] = event.get("content") or ""
                elif et == "error":
                    result["error"] = event.get("message", "summary error")
                    return result

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
                    result["rewrite_error"] = event.get("message", "rewrite error")
        result["article"] = article

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()

    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_meta = []
    for url in TEST_VIDEOS:
        bvid = bvid_from_url(url)
        print(f"\n=== Metadata: {bvid} ===")
        try:
            meta = fetch_metadata(url)
            all_meta.append(meta)
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            (OUT_DIR / f"{bvid}_meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            print(f"Metadata failed: {e}")
            all_meta.append({"bvid": bvid, "error": str(e)})

    suffix = "_after_fix"
    for url in TEST_VIDEOS:
        bvid = bvid_from_url(url)
        print(f"\n=== Analysis: {bvid} ===")
        result = run_analysis(url, suffix="_after_fix")
        out_path = OUT_DIR / f"{bvid}{suffix}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  source={result.get('transcript_source')} segments={result.get('segment_count')} error={result.get('error')}")
        print(f"  written {out_path}")

    (OUT_DIR / "ground_truth.json").write_text(
        json.dumps(GROUND_TRUTH, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "all_meta.json").write_text(
        json.dumps(all_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
