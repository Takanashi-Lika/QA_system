import json

from common.exceptions import NotFoundError
from infrastructure.database import get_cursor


def get_logistics(user_id, order_id=None):
    if order_id:
        return _get_single_logistics(user_id, order_id)
    return _get_all_logistics(user_id)


def _get_single_logistics(user_id, order_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, user_id FROM orders WHERE id = %s",
            (order_id,),
        )
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["user_id"] != user_id:
            raise NotFoundError("订单不存在")

        cur.execute(
            """
            SELECT tracking_number, carrier, status, current_location, estimated_delivery, timeline
            FROM logistics_records
            WHERE order_id = %s
            """,
            (order_id,),
        )
        record = cur.fetchone()

    if not record:
        raise NotFoundError("该订单暂无物流信息")

    return _format_record(record)


def _get_all_logistics(user_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT lr.tracking_number, lr.carrier, lr.status, lr.current_location,
                   lr.estimated_delivery, lr.timeline, lr.order_id
            FROM logistics_records lr
            JOIN orders o ON lr.order_id = o.id
            WHERE o.user_id = %s
            ORDER BY lr.order_id DESC
            """,
            (user_id,),
        )
        records = cur.fetchall()

    result = []
    for record in records:
        item = _format_record(record)
        item["order_id"] = record["order_id"]
        result.append(item)

    return result


def _format_record(record):
    record = dict(record)
    record["estimated_delivery"] = record["estimated_delivery"].isoformat() if record.get("estimated_delivery") else None
    timeline = record.get("timeline")
    if isinstance(timeline, str):
        record["timeline"] = json.loads(timeline)
    return record
