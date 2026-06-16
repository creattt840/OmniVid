import re
from enum import Enum
from typing import Self

from pydantic import BaseModel, field_validator, model_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(v: str) -> str:
    email = v.strip().lower()
    if not EMAIL_RE.match(email):
        raise ValueError("请输入有效的邮箱地址")
    return email


def _validate_password(v: str) -> str:
    if len(v) < 6:
        raise ValueError("密码至少 6 位")
    return v


class CodePurpose(str, Enum):
    register = "register"
    login = "login"
    reset_password = "reset_password"


class SendCodeRequest(BaseModel):
    email: str
    purpose: CodePurpose

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)


class RegisterRequest(BaseModel):
    email: str
    password: str
    code: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        code = v.strip()
        if not code.isdigit() or len(code) < 4:
            raise ValueError("请输入有效的验证码")
        return code


class LoginRequest(BaseModel):
    email: str
    password: str | None = None
    code: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        code = v.strip()
        if not code.isdigit() or len(code) < 4:
            raise ValueError("请输入有效的验证码")
        return code

    @model_validator(mode="after")
    def validate_login_method(self) -> Self:
        has_password = bool(self.password)
        has_code = bool(self.code)
        if has_password == has_code:
            raise ValueError("请使用密码或验证码其中一种方式登录")
        if has_password:
            _validate_password(self.password)
        return self


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        code = v.strip()
        if not code.isdigit() or len(code) < 4:
            raise ValueError("请输入有效的验证码")
        return code
