from pydantic import BaseModel


class SubtitleDownloadRequest(BaseModel):
    url: str
    format: str = "srt"


class TranslateRequest(BaseModel):
    url: str
    target_lang: str = "en"
    format: str = "srt"
