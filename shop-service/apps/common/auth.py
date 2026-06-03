import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Header, Depends

from common.exceptions import AuthenticationError, PermissionDeniedError


JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-internal-token-change-in-production")


def create_token(user_id: int, email: str, role: str) -> str:
    """签发JWT Token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def get_current_user(authorization: str = Header(None)) -> dict:
    """从Authorization Header解码JWT，返回 {user_id, email, role}"""
    if not authorization:
        raise AuthenticationError("未登录或Token过期")
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise AuthenticationError("认证格式错误")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "role": payload["role"],
        }
    except (ValueError, jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise AuthenticationError("未登录或Token过期")


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    """校验管理员角色，不通过返回403"""
    if user.get("role") != "admin":
        raise PermissionDeniedError("需要管理员权限")
    return user


def verify_internal_token(x_internal_token: str = Header(..., alias="X-Internal-Token")) -> bool:
    """校验内部接口Token"""
    if x_internal_token != INTERNAL_API_TOKEN:
        raise AuthenticationError("无效的内部接口Token")
    return True
