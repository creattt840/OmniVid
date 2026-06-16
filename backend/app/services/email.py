import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings

PURPOSE_LABELS = {
    "register": "注册账号",
    "login": "登录",
    "reset_password": "重置密码",
}


def send_verification_email(to_email: str, code: str, purpose: str) -> None:
    settings = get_settings()
    if not settings.smtp_user or not settings.smtp_password:
        raise RuntimeError("邮件发送失败，请检查 SMTP 配置")

    label = PURPOSE_LABELS.get(purpose, "验证")
    subject = f"OmniVid 验证码 — {label}"
    text_body = (
        f"您的 OmniVid 验证码是：{code}\n\n"
        f"用途：{label}\n"
        f"验证码 {settings.verify_code_expire_minutes} 分钟内有效，请勿泄露给他人。\n\n"
        f"如非本人操作，请忽略此邮件。"
    )
    html_body = (
        f"<p>您的 OmniVid 验证码是：</p>"
        f"<p style='font-size:24px;font-weight:bold;letter-spacing:4px;'>{code}</p>"
        f"<p>用途：{label}</p>"
        f"<p>验证码 {settings.verify_code_expire_minutes} 分钟内有效，请勿泄露给他人。</p>"
        f"<p style='color:#888;'>如非本人操作，请忽略此邮件。</p>"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, [to_email], msg.as_string())
    except Exception as exc:
        raise RuntimeError("邮件发送失败，请检查 SMTP 配置") from exc
