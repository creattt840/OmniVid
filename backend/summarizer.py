"""DeepSeek AI 摘要、思维导图、问答 + Session 管理 + SSE"""

import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Generator, Optional

from openai import OpenAI

from subtitles import SubtitleFetcher

logger = logging.getLogger("summarizer")

SESSION_TTL = 30 * 60  # 30 minutes
MAX_TRANSCRIPT_CHARS = 50000


@dataclass
class AnalysisSession:
    session_id: str
    url: str
    title: str
    duration: int
    platform: str
    transcript_source: str  # subtitle | whisper
    segments: list
    created_at: float = field(default_factory=time.time)
    summary: Optional[dict] = None
    chat_history: list = field(default_factory=list)


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, AnalysisSession] = {}

    def create(self, **kwargs) -> AnalysisSession:
        session = AnalysisSession(session_id=str(uuid.uuid4()), **kwargs)
        self._sessions[session.session_id] = session
        self.cleanup_expired()
        return session

    def get(self, session_id: str) -> Optional[AnalysisSession]:
        self.cleanup_expired()
        return self._sessions.get(session_id)

    def cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if now - s.created_at > SESSION_TTL]
        for sid in expired:
            del self._sessions[sid]


session_store = SessionStore()

SUMMARY_SYSTEM_PROMPT = """你是一位专业的视频内容分析师。根据提供的视频转录文本，生成结构化分析。
必须严格输出 JSON，不要包含 markdown 代码块或其他文字。JSON 格式如下：
{
  "summary": "200-400字的视频摘要",
  "highlights": ["要点1", "要点2", "要点3", "要点4", "要点5"],
  "chapters": [{"time": "00:00", "title": "章节标题", "summary": "章节摘要"}],
  "mindmap": "# 主题\\n## 分支1\\n### 细节\\n## 分支2",
  "terms": [{"term": "术语", "definition": "解释"}]
}
要求：highlights 5条；chapters 3-8个；mindmap 用 Markdown 层级列表；terms 2-5个。"""

CHAT_SYSTEM_PROMPT = """你是一位视频内容助手。根据提供的视频转录和摘要，准确回答用户关于视频内容的问题。
如果视频中没有相关信息，请诚实说明。回答简洁清晰，使用中文。"""


class VideoAnalyzer:
    def __init__(
        self,
        subtitle_fetcher: SubtitleFetcher,
        transcriber=None,
    ):
        self.subtitles = subtitle_fetcher
        self.transcriber = transcriber
        self.client = self._init_client()

    @staticmethod
    def _init_client() -> Optional[OpenAI]:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return None
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        return OpenAI(api_key=api_key, base_url=base_url)

    def is_ai_available(self) -> bool:
        return self.client is not None

    def prepare_transcript(self, url: str) -> AnalysisSession:
        segments, meta = self.subtitles.fetch_from_url(url)
        source = "subtitle"

        if not segments and self.transcriber:
            try:
                segments, meta = self.transcriber.transcribe_url(url)
                source = "whisper"
            except ValueError as e:
                raise ValueError(f"无法获取视频转录文本：{e}") from e

        if not segments:
            raise ValueError("无法获取视频转录文本（无字幕且语音转写失败）")

        return session_store.create(
            url=url,
            title=meta.get("title") or "未知标题",
            duration=meta.get("duration") or 0,
            platform=meta.get("platform") or "Unknown",
            transcript_source=source,
            segments=segments,
        )

    def _build_transcript_text(self, session: AnalysisSession) -> str:
        text = SubtitleFetcher.segments_to_text(session.segments)
        if len(text) > MAX_TRANSCRIPT_CHARS:
            text = text[:MAX_TRANSCRIPT_CHARS] + "\n...(内容已截断)"
        return text

    def stream_summary(self, session_id: str) -> Generator[str, None, None]:
        session = session_store.get(session_id)
        if not session:
            yield self._sse("error", {"message": "会话不存在或已过期"})
            return

        if not self.client:
            yield self._sse("error", {"message": "未配置 DEEPSEEK_API_KEY，请在 backend/.env 中设置"})
            return

        transcript = self._build_transcript_text(session)
        yield self._sse("transcript", {"segments": session.segments, "text": transcript})

        user_prompt = f"视频标题：{session.title}\n平台：{session.platform}\n\n转录文本：\n{transcript}"

        try:
            stream = self.client.chat.completions.create(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                temperature=0.3,
            )

            full_content = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_content += delta
                    yield self._sse("summary_chunk", {"content": delta})

            summary_data = self._parse_summary_json(full_content)
            session.summary = summary_data
            yield self._sse("summary_done", summary_data)
            yield self._sse("mindmap", {"content": summary_data.get("mindmap", "")})

        except Exception as e:
            logger.exception("摘要生成失败")
            yield self._sse("error", {"message": f"AI 摘要生成失败: {str(e)}"})

    def stream_chat(self, session_id: str, message: str) -> Generator[str, None, None]:
        session = session_store.get(session_id)
        if not session:
            yield self._sse("error", {"message": "会话不存在或已过期"})
            return

        if not self.client:
            yield self._sse("error", {"message": "未配置 DEEPSEEK_API_KEY"})
            return

        transcript = self._build_transcript_text(session)
        summary_ctx = ""
        if session.summary:
            summary_ctx = json.dumps(session.summary, ensure_ascii=False, indent=2)

        system_content = (
            f"{CHAT_SYSTEM_PROMPT}\n\n"
            f"视频标题：{session.title}\n\n"
            f"视频摘要：\n{summary_ctx}\n\n"
            f"转录文本：\n{transcript}"
        )

        messages = [{"role": "system", "content": system_content}]
        for turn in session.chat_history:
            messages.append(turn)
        messages.append({"role": "user", "content": message})

        try:
            stream = self.client.chat.completions.create(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                messages=messages,
                stream=True,
                temperature=0.5,
            )

            full_reply = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_reply += delta
                    yield self._sse("chat_chunk", {"content": delta})

            session.chat_history.append({"role": "user", "content": message})
            session.chat_history.append({"role": "assistant", "content": full_reply})
            yield self._sse("chat_done", {"content": full_reply})

        except Exception as e:
            logger.exception("问答失败")
            yield self._sse("error", {"message": f"AI 问答失败: {str(e)}"})

    @staticmethod
    def _parse_summary_json(content: str) -> dict:
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                pass

        return {
            "summary": content[:500],
            "highlights": [],
            "chapters": [],
            "mindmap": "# 视频内容\n## 详见摘要",
            "terms": [],
        }

    @staticmethod
    def _sse(event_type: str, data: dict) -> str:
        payload = {"type": event_type, **data}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
