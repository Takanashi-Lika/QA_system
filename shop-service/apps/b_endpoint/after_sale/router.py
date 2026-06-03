from fastapi import APIRouter, Depends, Query

from apps.b_endpoint.after_sale.schema import ReviewAfterSaleRequest
from apps.common.auth import get_current_admin
from infrastructure.database import get_cursor

router = APIRouter(prefix="/b-endpoint/after-sales", tags=["B端-售后管理"], dependencies=[Depends(get_current_admin)])


@router.get("/")
def list_all_after_sales(
    status: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * size
    with get_cursor() as cur:
        if status:
            cur.execute(
                """
                SELECT id, order_id, user_id, reason, status, created_at, updated_at
                FROM after_sale_requests
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (status, size, offset),
            )
            rows = cur.fetchall()
            cur.execute(
                "SELECT COUNT(*) AS total FROM after_sale_requests WHERE status = %s",
                (status,),
            )
        else:
            cur.execute(
                """
                SELECT id, order_id, user_id, reason, status, created_at, updated_at
                FROM after_sale_requests
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (size, offset),
            )
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) AS total FROM after_sale_requests")

        total = cur.fetchone()["total"]

    records = []
    for row in rows:
        rec = dict(row)
        rec["created_at"] = rec["created_at"].isoformat() if rec["created_at"] else None
        rec["updated_at"] = rec["updated_at"].isoformat() if rec.get("updated_at") else None
        records.append(rec)

    return {"code": 0, "message": "success", "data": {"items": records, "total": total, "page": page, "size": size}}


@router.put("/{request_id}")
def review_after_sale(request_id: int, body: ReviewAfterSaleRequest):
    return {"code": 0, "message": "售后审核功能暂未开放", "data": None}
