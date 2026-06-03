import bcrypt

from infrastructure.database import get_cursor
from common.exceptions import ValidationError, AuthenticationError, NotFoundError
from apps.common.auth import create_token


def register_user(email: str, password: str, nickname: str) -> dict:
    with get_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone() is not None:
            raise ValidationError("邮箱已注册")

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cur.execute(
            "INSERT INTO users (email, password, nickname, role) VALUES (%s, %s, %s, %s) RETURNING id, email, nickname, role, address, created_at, updated_at",
            (email, hashed, nickname, "user"),
        )
        user = cur.fetchone()
        return dict(user)


def login_user(email: str, password: str) -> dict:
    with get_cursor() as cur:
        cur.execute("SELECT id, email, password, nickname, role, address, created_at, updated_at FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user is None:
            raise AuthenticationError("邮箱或密码错误")

        if not bcrypt.checkpw(password.encode(), user["password"].encode()):
            raise AuthenticationError("邮箱或密码错误")

        token = create_token(user["id"], user["email"], user["role"])

        user_info = dict(user)
        del user_info["password"]
        return {"token": token, "user": user_info}


def get_user_profile(user_id: int) -> dict:
    with get_cursor() as cur:
        cur.execute("SELECT id, email, nickname, role, address, created_at, updated_at FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if user is None:
            raise NotFoundError("用户不存在")
        return dict(user)


def update_address(user_id: int, address: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE users SET address = %s, updated_at = NOW() WHERE id = %s RETURNING id, email, nickname, role, address, created_at, updated_at",
            (address, user_id),
        )
        user = cur.fetchone()
        return dict(user)
