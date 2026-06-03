from fastapi import APIRouter, Depends, Query

from apps.common.auth import get_current_admin
from infrastructure.database import get_cursor

router = APIRouter(prefix="/b-endpoint/orders", tags=["B端-订单管理"], dependencies=[Depends(get_current_admin)])


@router.get("/")
def list_all_orders(
    status: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * size
    with get_cursor() as cur:
        if status:
            cur.execute(
                """
                SELECT id, user_id, total_amount, status, address, created_at, paid_at, cancelled_at
                FROM orders
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (status, size, offset),
            )
            rows = cur.fetchall()
            cur.execute(
                "SELECT COUNT(*) AS total FROM orders WHERE status = %s",
                (status,),
            )
        else:
            cur.execute(
                """
                SELECT id, user_id, total_amount, status, address, created_at, paid_at, cancelled_at
                FROM orders
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (size, offset),
            )
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) AS total FROM orders")

        total = cur.fetchone()["total"]

    orders = []
    for row in rows:
        order = dict(row)
        order["total_amount"] = float(order["total_amount"])
        order["created_at"] = order["created_at"].isoformat() if order["created_at"] else None
        order["paid_at"] = order["paid_at"].isoformat() if order.get("paid_at") else None
        order["cancelled_at"] = order["cancelled_at"].isoformat() if order.get("cancelled_at") else None
        orders.append(order)

    return {"code": 0, "message": "success", "data": {"items": orders, "total": total, "page": page, "size": size}}
