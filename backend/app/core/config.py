import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """集中管理环境变量配置。"""

    database_url: str
    jwt_secret: str
    jwt_expire_days: int
    free_daily_ai_limit: int
    vip_duration_days: int
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    whisper_model: str
    whisper_max_duration: int
    upload_max_size_mb: int
    upload_max_duration: int
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_id: str
    frontend_url: str
    ytdlp_proxy: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_use_ssl: bool
    verify_code_length: int
    verify_code_expire_minutes: int
    verify_code_resend_seconds: int

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./omnivid.db")
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-change-me-in-production")
        self.jwt_expire_days = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
        self.free_daily_ai_limit = int(os.getenv("FREE_DAILY_AI_LIMIT", "10"))
        self.vip_duration_days = int(os.getenv("VIP_DURATION_DAYS", "30"))
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.whisper_model = os.getenv("WHISPER_MODEL", "small")
        self.whisper_max_duration = int(os.getenv("WHISPER_MAX_DURATION", "3600"))
        self.upload_max_size_mb = int(os.getenv("UPLOAD_MAX_SIZE_MB", "500"))
        upload_max = os.getenv("UPLOAD_MAX_DURATION")
        self.upload_max_duration = int(upload_max) if upload_max else self.whisper_max_duration
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.stripe_price_id = os.getenv("STRIPE_PRICE_ID", "")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.ytdlp_proxy = (
            os.getenv("YTDLP_PROXY", "").strip()
            or os.getenv("HTTPS_PROXY", "").strip()
            or os.getenv("HTTP_PROXY", "").strip()
        )
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.qq.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "") or self.smtp_user
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() in ("1", "true", "yes")
        self.verify_code_length = int(os.getenv("VERIFY_CODE_LENGTH", "6"))
        self.verify_code_expire_minutes = int(os.getenv("VERIFY_CODE_EXPIRE_MINUTES", "5"))
        self.verify_code_resend_seconds = int(os.getenv("VERIFY_CODE_RESEND_SECONDS", "60"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
