from fastapi import APIRouter, Depends

from apps.c_endpoint.user.schema import RegisterRequest, LoginRequest, UpdateAddressRequest
from apps.common.auth import get_current_user
from domain.user.user_service import register_user, login_user, get_user_profile, update_address

router = APIRouter(prefix="/c-endpoint", tags=["C端-用户"])


@router.post("/register")
def register(req: RegisterRequest):
    user = register_user(req.email, req.password, req.nickname)
    return {"code": 0, "data": user, "message": "success"}


@router.post("/login")
def login(req: LoginRequest):
    result = login_user(req.email, req.password)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    user = get_user_profile(current_user["user_id"])
    return {"code": 0, "data": user, "message": "success"}


@router.put("/address")
def update_user_address(req: UpdateAddressRequest, current_user: dict = Depends(get_current_user)):
    user = update_address(current_user["user_id"], req.address)
    return {"code": 0, "data": user, "message": "success"}
