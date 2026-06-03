from common.exceptions import NotFoundError, BusinessError
from infrastructure.database import get_cursor


def create_after_sale(user_id, order_id, as_type, reason):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, user_id, status FROM orders WHERE id = %s",
            (order_id,),
        )
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["user_id"] != user_id:
            raise NotFoundError("订单不存在")
        if order["status"] != "paid":
            raise BusinessError("仅已支付订单可申请售后")

        cur.execute(
            """
            INSERT INTO shop.after_sale_requests (user_id, order_id, type, reason, status, created_at)
            VALUES (%s, %s, %s, %s, 'pending', NOW())
            RETURNING id, user_id, order_id, type, reason, status, created_at
            """,
            (user_id, order_id, as_type, reason),
        )
        row = cur.fetchone()

    result = dict(row)
    result["created_at"] = result["created_at"].isoformat() if result.get("created_at") else None
    return result


def get_after_sales(user_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, order_id, type, reason, status, created_at
            FROM shop.after_sale_requests
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    result = []
    for row in rows:
        item = dict(row)
        item["created_at"] = item["created_at"].isoformat() if item.get("created_at") else None
        result.append(item)

    return result
