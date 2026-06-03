from fastapi import APIRouter, Depends

from apps.c_endpoint.cart.schema import AddCartItemRequest, UpdateCartItemRequest
from apps.common.auth import get_current_user
from domain.cart.cart_service import add_to_cart, update_cart_item, remove_from_cart, get_cart

router = APIRouter(prefix="/c-endpoint/cart", tags=["C端-购物车"])


@router.get("/")
def view_cart(current_user: dict = Depends(get_current_user)):
    result = get_cart(current_user["user_id"])
    return {"code": 0, "message": "success", "data": result}


@router.post("/")
def add_item(req: AddCartItemRequest, current_user: dict = Depends(get_current_user)):
    item = add_to_cart(current_user["user_id"], req.product_id, req.quantity)
    return {"code": 0, "message": "success", "data": item}


@router.put("/{product_id}")
def update_item(product_id: int, req: UpdateCartItemRequest, current_user: dict = Depends(get_current_user)):
    item = update_cart_item(current_user["user_id"], product_id, req.quantity)
    return {"code": 0, "message": "success", "data": item}


@router.delete("/{product_id}")
def remove_item(product_id: int, current_user: dict = Depends(get_current_user)):
    remove_from_cart(current_user["user_id"], product_id)
    return {"code": 0, "message": "success"}
