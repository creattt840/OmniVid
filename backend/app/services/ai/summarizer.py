"""DeepSeek AI 摘要、思维导图、问答 + Session 管理 + SSE"""

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Generator, Optional

from openai import OpenAI

from app.services.ai.subtitles import SubtitleFetcher, parse_subtitle_file
from app.services.ai.summary_parser import extract_partial_summary, parse_summary_json
from app.services.ai.transcript_quality import assert_transcript_quality
from app.core.config import get_settings

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
要求：highlights 5条；chapters 3-8个；mindmap 用 Markdown 层级列表；terms 2-5个。
若转录文本仅为音乐标签、歌词碎片、无意义重复，或明显不足以描述视频内容，不要编造——在 summary 中明确写「转录内容不足，无法生成可靠分析」并将 highlights/chapters/terms 设为空数组。"""

CHAT_SYSTEM_PROMPT = """你是一位视频内容助手。根据提供的视频转录和摘要，准确回答用户关于视频内容的问题。
如果视频中没有相关信息，请诚实说明。回答简洁清晰，使用中文。"""

REWRITE_SYSTEM_PROMPT = """你是一位专业的内容编辑。将口语化的视频转录文本改写成结构清晰、语言流畅的书面文章。
要求：
- 保留原意，去除口语赘词和重复
- 使用 Markdown 格式，含适当小标题与段落
- 800-1500 字，中文输出
- 不要添加视频中没有的信息"""

TRANSLATE_SYSTEM_PROMPT = """你是一位专业翻译。将字幕文本翻译为目标语言，保持原意与时间戳对应关系。
必须严格输出 JSON 数组，不要包含 markdown 或其他文字：
[{"start": 0.0, "end": 5.0, "text": "翻译后的文本"}, ...]
start/end 与输入完全一致，仅翻译 text 字段。"""


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
        settings = get_settings()
        if not settings.deepseek_api_key:
            return None
        return OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

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

        assert_transcript_quality(segments, meta.get("duration") or 0)

        return session_store.create(
            url=url,
            title=meta.get("title") or "未知标题",
            duration=meta.get("duration") or 0,
            platform=meta.get("platform") or "Unknown",
            transcript_source=source,
            segments=segments,
        )

    def prepare_transcript_from_file(self, record) -> AnalysisSession:
        """从本地上传记录准备转录：优先外挂字幕，否则 Whisper。"""
        from app.services.upload.local_upload import UploadRecord

        if not isinstance(record, UploadRecord):
            raise ValueError("无效的上传记录")

        meta = {
            "title": record.title,
            "duration": record.duration,
            "platform": "本地文件",
        }
        segments: list = []
        source = "subtitle"

        if record.subtitle_path and record.subtitle_path.exists():
            content = record.subtitle_path.read_text(encoding="utf-8", errors="replace")
            ext = record.subtitle_path.suffix.lstrip(".").lower()
            segments = parse_subtitle_file(content, ext)
            if not segments:
                raise ValueError("外挂字幕文件解析失败，请检查格式")

        if not segments:
            if not self.transcriber:
                raise ValueError("无法获取视频转录文本（无字幕且未配置转写引擎）")
            try:
                segments, meta = self.transcriber.transcribe_file(
                    record.media_path,
                    meta=meta,
                )
                source = "whisper"
            except ValueError as e:
                raise ValueError(f"无法获取视频转录文本：{e}") from e

        if not segments:
            raise ValueError("无法获取视频转录文本（无字幕且语音转写失败）")

        # 用户主动上传的外挂字幕信任度更高，不做平台自动字幕/Whisper 同款门控
        if source == "whisper":
            assert_transcript_quality(segments, meta.get("duration") or record.duration or 0)

        file_ref = f"local://{record.file_id}"
        return session_store.create(
            url=file_ref,
            title=meta.get("title") or record.title,
            duration=meta.get("duration") or record.duration,
            platform="本地文件",
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
                model=get_settings().deepseek_model,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                temperature=0.3,
                max_tokens=8192,
            )

            full_content = ""
            prev_summary_len = 0
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_content += delta
                    # 仅流式输出 summary 字段的纯文本，避免前端展示原始 JSON
                    current_summary = extract_partial_summary(full_content)
                    if len(current_summary) > prev_summary_len:
                        yield self._sse(
                            "summary_chunk",
                            {"content": current_summary[prev_summary_len:]},
                        )
                        prev_summary_len = len(current_summary)

            summary_data = parse_summary_json(full_content)
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
                model=get_settings().deepseek_model,
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

    def stream_chat_from_context(
        self,
        title: str,
        segments: list,
        summary: dict | None,
        chat_history: list,
        message: str,
    ) -> Generator[str, None, None]:
        """基于持久化上下文进行问答，chat_history 会被原地更新。"""
        if not self.client:
            yield self._sse("error", {"message": "未配置 DEEPSEEK_API_KEY"})
            return

        if not segments:
            yield self._sse("error", {"message": "历史记录缺少转录文本，无法继续问答"})
            return

        text = SubtitleFetcher.segments_to_text(segments)
        if len(text) > MAX_TRANSCRIPT_CHARS:
            text = text[:MAX_TRANSCRIPT_CHARS] + "\n...(内容已截断)"

        summary_ctx = json.dumps(summary or {}, ensure_ascii=False, indent=2)
        system_content = (
            f"{CHAT_SYSTEM_PROMPT}\n\n"
            f"视频标题：{title}\n\n"
            f"视频摘要：\n{summary_ctx}\n\n"
            f"转录文本：\n{text}"
        )

        messages = [{"role": "system", "content": system_content}]
        for turn in chat_history:
            messages.append(turn)
        messages.append({"role": "user", "content": message})

        try:
            stream = self.client.chat.completions.create(
                model=get_settings().deepseek_model,
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

            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": full_reply})
            yield self._sse("chat_done", {"content": full_reply})

        except Exception as e:
            logger.exception("历史问答失败")
            yield self._sse("error", {"message": f"AI 问答失败: {str(e)}"})

    def stream_rewrite_from_context(self, title: str, segments: list) -> Generator[str, None, None]:
        """基于持久化转录文本生成改写文章。"""
        if not self.client:
            yield self._sse("error", {"message": "未配置 DEEPSEEK_API_KEY"})
            return

        if not segments:
            yield self._sse("error", {"message": "历史记录缺少转录文本，无法生成改写文章"})
            return

        text = SubtitleFetcher.segments_to_text(segments)
        if len(text) > MAX_TRANSCRIPT_CHARS:
            text = text[:MAX_TRANSCRIPT_CHARS] + "\n...(内容已截断)"

        user_prompt = f"视频标题：{title}\n\n转录文本：\n{text}"

        try:
            stream = self.client.chat.completions.create(
                model=get_settings().deepseek_model,
                messages=[
                    {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                temperature=0.4,
                max_tokens=4096,
            )

            full_content = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_content += delta
                    yield self._sse("rewrite_chunk", {"content": delta})

            yield self._sse("rewrite_done", {"content": full_content})

        except Exception as e:
            logger.exception("历史文章改写失败")
            yield self._sse("error", {"message": f"AI 改写失败: {str(e)}"})

    def stream_rewrite(self, session_id: str) -> Generator[str, None, None]:
        session = session_store.get(session_id)
        if not session:
            yield self._sse("error", {"message": "会话不存在或已过期"})
            return

        if not self.client:
            yield self._sse("error", {"message": "未配置 DEEPSEEK_API_KEY"})
            return

        transcript = self._build_transcript_text(session)
        user_prompt = f"视频标题：{session.title}\n\n转录文本：\n{transcript}"

        try:
            stream = self.client.chat.completions.create(
                model=get_settings().deepseek_model,
                messages=[
                    {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                temperature=0.4,
                max_tokens=4096,
            )

            full_content = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_content += delta
                    yield self._sse("rewrite_chunk", {"content": delta})

            yield self._sse("rewrite_done", {"content": full_content})

        except Exception as e:
            logger.exception("文章改写失败")
            yield self._sse("error", {"message": f"AI 改写失败: {str(e)}"})

    def translate_segments(
        self, segments: list, target_lang: str = "en"
    ) -> list:
        if not self.client:
            raise ValueError("未配置 DEEPSEEK_API_KEY")

        lang_map = {
            "en": "English",
            "zh": "简体中文",
            "ja": "Japanese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
        }
        target = lang_map.get(target_lang, target_lang)

        # 分批翻译，避免超长上下文
        batch_size = 40
        result = []
        for i in range(0, len(segments), batch_size):
            batch = segments[i : i + batch_size]
            batch_json = json.dumps(
                [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in batch],
                ensure_ascii=False,
            )
            resp = self.client.chat.completions.create(
                model=get_settings().deepseek_model,
                messages=[
                    {"role": "system", "content": TRANSLATE_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"目标语言：{target}\n\n字幕：\n{batch_json}",
                    },
                ],
                temperature=0.2,
                max_tokens=8192,
            )
            content = resp.choices[0].message.content or "[]"
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            translated = json.loads(content)
            result.extend(translated)

        return result

    @staticmethod
    def _sse(event_type: str, data: dict) -> str:
        payload = {"type": event_type, **data}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
