from typing import Optional

from pydantic import BaseModel, model_validator


class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    file_id: Optional[str] = None

    @model_validator(mode="after")
    def check_one_of(self):
        has_url = bool(self.url and self.url.strip())
        has_file = bool(self.file_id and self.file_id.strip())
        if has_url == has_file:
            raise ValueError("请提供 url 或 file_id 其中之一")
        return self


class ChatRequest(BaseModel):
    message: str
