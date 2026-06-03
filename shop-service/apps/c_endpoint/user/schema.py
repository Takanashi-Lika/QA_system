from pydantic import BaseModel, field_validator


class RegisterRequest(BaseModel):
    email: str
    password: str
    nickname: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("密码至少6位")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateAddressRequest(BaseModel):
    address: str

    @field_validator("address")
    @classmethod
    def address_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("收货地址不能为空")
        return v.strip()
