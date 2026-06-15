from typing import Any, Optional

from pydantic import BaseModel, field_validator


class SaveHistoryRequest(BaseModel):
    url: str
    source: Optional[str] = "url"
    title: Optional[str] = ""
    platform: Optional[str] = ""
    thumbnail: Optional[str] = None
    summary: Optional[dict[str, Any]] = None
    mindmap: Optional[str] = ""
    segments: Optional[list] = None
    article: Optional[str] = None
    chatHistory: Optional[list] = None
    transcriptSource: Optional[str] = None
    partial: Optional[bool] = False

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        url = v.strip()
        if not url:
            raise ValueError("url 不能为空")
        return url
