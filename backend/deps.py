from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth_utils import decode_access_token
from database import get_db
from membership import user_is_vip
from models import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": "请先登录", "code": "AUTH_REQUIRED"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": "登录已过期，请重新登录", "code": "AUTH_EXPIRED"},
        )
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": "用户不存在", "code": "AUTH_INVALID"},
        )
    return user


def require_vip(user: User = Depends(get_current_user)) -> User:
    if not user_is_vip(user):
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": "此功能需要 VIP 会员，请先开通 VIP",
                "code": "VIP_REQUIRED",
            },
        )
    return user
