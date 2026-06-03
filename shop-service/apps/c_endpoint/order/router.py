from fastapi import APIRouter, Depends, Query

from apps.c_endpoint.order.schema import CreateOrderRequest
from apps.common.auth import get_current_user
from domain.order.order_service import (
    create_order,
    pay_order,
    cancel_order,
    get_order_list,
    get_order_detail,
)

router = APIRouter(prefix="/c-endpoint/orders", tags=["C端-订单"])


@router.post("/")
def create(req: CreateOrderRequest, current_user: dict = Depends(get_current_user)):
    result = create_order(current_user["user_id"], req.address)
    return {"code": 0, "message": "success", "data": result}


@router.post("/{order_id}/pay")
def pay(order_id: int, current_user: dict = Depends(get_current_user)):
    result = pay_order(current_user["user_id"], order_id)
    return {"code": 0, "message": "success", "data": result}


@router.delete("/{order_id}")
def cancel(order_id: int, current_user: dict = Depends(get_current_user)):
    result = cancel_order(current_user["user_id"], order_id)
    return {"code": 0, "message": "success", "data": result}


@router.get("/")
def list_orders(
    status: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    result = get_order_list(current_user["user_id"], status=status, page=page, size=size)
    return {"code": 0, "message": "success", "data": result}


@router.get("/{order_id}")
def detail(order_id: int, current_user: dict = Depends(get_current_user)):
    result = get_order_detail(current_user["user_id"], order_id)
    return {"code": 0, "message": "success", "data": result}
