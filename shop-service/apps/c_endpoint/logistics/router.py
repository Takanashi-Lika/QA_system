from fastapi import APIRouter, Depends, Query

from apps.common.auth import get_current_user
from domain.logistics.logistics_service import get_logistics

router = APIRouter(prefix="/c-endpoint", tags=["C端-物流"])


@router.get("/logistics")
def logistics(
    order_id: int = Query(None),
    current_user: dict = Depends(get_current_user),
):
    result = get_logistics(current_user["user_id"], order_id=order_id)
    return {"code": 0, "message": "success", "data": result}
