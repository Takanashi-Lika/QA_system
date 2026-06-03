from fastapi import APIRouter, Depends

from apps.c_endpoint.after_sale.schema import CreateAfterSaleRequest
from apps.common.auth import get_current_user
from domain.after_sale.after_sale_service import create_after_sale, get_after_sales

router = APIRouter(prefix="/c-endpoint", tags=["C端-售后"])


@router.post("/after-sales")
def create(req: CreateAfterSaleRequest, current_user: dict = Depends(get_current_user)):
    result = create_after_sale(current_user["user_id"], req.order_id, req.type, req.reason)
    return {"code": 0, "message": "success", "data": result}


@router.get("/after-sales")
def list_after_sales(current_user: dict = Depends(get_current_user)):
    result = get_after_sales(current_user["user_id"])
    return {"code": 0, "message": "success", "data": result}
