import os
import json
import uuid

from common.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from common.logger import logger
from infrastructure.database import get_connection, release_connection, get_cursor
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta


def create_order(user_id, address):
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT ci.product_id, ci.quantity, p.name, p.price, p.stock, p.status
            FROM cart_items ci JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s
            """,
            (user_id,),
        )
        cart_items = cur.fetchall()
        if not cart_items:
            raise BusinessError("购物车为空")

        product_ids = [item["product_id"] for item in cart_items]
        cur.execute(
            "SELECT id, name, price, stock FROM products WHERE id = ANY(%s) FOR UPDATE",
            (product_ids,),
        )
        locked_products = {row["id"]: row for row in cur.fetchall()}

        total_amount = 0
        for item in cart_items:
            product = locked_products[item["product_id"]]
            if product["stock"] < item["quantity"]:
                raise BusinessError(f"商品 [{product['name']}] 库存不足")
            total_amount += product["price"] * item["quantity"]

        for item in cart_items:
            cur.execute(
                "UPDATE products SET stock = stock - %s, updated_at = NOW() WHERE id = %s AND stock >= %s",
                (item["quantity"], item["product_id"], item["quantity"]),
            )
            if cur.rowcount == 0:
                raise BusinessError("扣减库存失败，请重试")

        cur.execute(
            """INSERT INTO orders (user_id, total_amount, status, address, created_at)
               VALUES (%s,%s,'pending',%s,NOW()) RETURNING id, created_at""",
            (user_id, total_amount, address),
        )
        order_row = cur.fetchone()
        order_id = order_row["id"]
        created_at = order_row["created_at"]

        for item in cart_items:
            product = locked_products[item["product_id"]]
            cur.execute(
                """INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                   VALUES (%s,%s,%s,%s,%s) RETURNING id""",
                (order_id, item["product_id"], product["name"], product["price"], item["quantity"]),
            )

        cur.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))

        conn.commit()

        order = {
            "id": order_id,
            "user_id": user_id,
            "total_amount": float(total_amount),
            "status": "pending",
            "address": address,
            "created_at": created_at.isoformat() if created_at else None,
            "items": [],
        }
        for item in cart_items:
            product = locked_products[item["product_id"]]
            order["items"].append({
                "product_id": item["product_id"],
                "product_name": product["name"],
                "price": float(product["price"]),
                "quantity": item["quantity"],
            })
        return order

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)


def pay_order(user_id, order_id):
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, user_id, status, total_amount FROM orders WHERE id = %s FOR UPDATE",
            (order_id,),
        )
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["user_id"] != user_id:
            raise PermissionDeniedError("无权操作此订单")
        if order["status"] == "paid":
            raise BusinessError("请勿重复支付")
        if order["status"] == "cancelled":
            raise BusinessError("订单已取消，无法支付")
        if order["status"] != "pending":
            raise BusinessError("订单状态不允许支付")

        cur.execute(
            "UPDATE orders SET status='paid', paid_at=NOW() WHERE id=%s RETURNING paid_at",
            (order_id,),
        )
        paid_row = cur.fetchone()

        cur.execute(
            "INSERT INTO payment_records (order_id, amount, method, status) VALUES (%s,%s,'mock','success') RETURNING id",
            (order_id, order["total_amount"]),
        )

        tracking = f"SF{uuid.uuid4().hex[:10].upper()}"
        cur.execute(
            """INSERT INTO logistics_records (order_id, tracking_number, carrier, status, current_location, estimated_delivery, timeline)
               VALUES (%s,%s,'SF-Express','picked_up','深圳市南山区仓库',NOW() + INTERVAL '3 days',
               %s::JSONB)""",
            (order_id, tracking, json.dumps([
                {"time": datetime.now(timezone.utc).isoformat(), "status": "picked_up", "location": "深圳市南山区仓库"}
            ])),
        )

        conn.commit()

        return {
            "id": order_id,
            "status": "paid",
            "paid_at": paid_row["paid_at"].isoformat() if paid_row["paid_at"] else None,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)


def cancel_order(user_id, order_id):
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, user_id, status FROM orders WHERE id=%s FOR UPDATE", (order_id,))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["user_id"] != user_id:
            raise PermissionDeniedError("无权操作此订单")
        if order["status"] == "paid":
            raise BusinessError("订单已支付，不可取消")
        if order["status"] == "cancelled":
            raise BusinessError("订单已取消")
        if order["status"] != "pending":
            raise BusinessError("订单状态不允许取消")

        cur.execute("SELECT product_id, quantity FROM order_items WHERE order_id=%s", (order_id,))
        items = cur.fetchall()
        for item in items:
            cur.execute(
                "UPDATE products SET stock = stock + %s, updated_at = NOW() WHERE id = %s",
                (item["quantity"], item["product_id"]),
            )

        cur.execute(
            "UPDATE orders SET status='cancelled', cancelled_at=NOW() WHERE id=%s RETURNING cancelled_at",
            (order_id,),
        )
        cancelled_row = cur.fetchone()

        conn.commit()

        return {
            "id": order_id,
            "status": "cancelled",
            "cancelled_at": cancelled_row["cancelled_at"].isoformat() if cancelled_row["cancelled_at"] else None,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)


def get_order_list(user_id, status=None, page=1, size=20):
    offset = (page - 1) * size
    with get_cursor() as cur:
        if status:
            cur.execute(
                """
                SELECT id, user_id, total_amount, status, address, created_at, paid_at, cancelled_at
                FROM orders
                WHERE user_id = %s AND status = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, status, size, offset),
            )
            cur.execute(
                "SELECT COUNT(*) AS total FROM orders WHERE user_id = %s AND status = %s",
                (user_id, status),
            )
        else:
            cur.execute(
                """
                SELECT id, user_id, total_amount, status, address, created_at, paid_at, cancelled_at
                FROM orders
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, size, offset),
            )
            cur.execute(
                "SELECT COUNT(*) AS total FROM orders WHERE user_id = %s",
                (user_id,),
            )

        rows = cur.fetchall()
        total = cur.fetchone()["total"]

    orders = []
    for row in rows:
        order = dict(row)
        order["total_amount"] = float(order["total_amount"])
        order["created_at"] = order["created_at"].isoformat() if order["created_at"] else None
        order["paid_at"] = order["paid_at"].isoformat() if order.get("paid_at") else None
        order["cancelled_at"] = order["cancelled_at"].isoformat() if order.get("cancelled_at") else None
        orders.append(order)

    return {
        "items": orders,
        "total": total,
        "page": page,
        "size": size,
    }


def get_order_detail(user_id, order_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, total_amount, status, address, created_at, paid_at, cancelled_at
            FROM orders
            WHERE id = %s
            """,
            (order_id,),
        )
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["user_id"] != user_id:
            raise NotFoundError("订单不存在")

        cur.execute(
            """
            SELECT id, product_id, product_name, price, quantity
            FROM order_items
            WHERE order_id = %s
            """,
            (order_id,),
        )
        items = cur.fetchall()

    order_data = dict(order)
    order_data["total_amount"] = float(order_data["total_amount"])
    order_data["created_at"] = order_data["created_at"].isoformat() if order_data["created_at"] else None
    order_data["paid_at"] = order_data["paid_at"].isoformat() if order_data.get("paid_at") else None
    order_data["cancelled_at"] = order_data["cancelled_at"].isoformat() if order_data.get("cancelled_at") else None
    order_data["items"] = []
    for item in items:
        item_data = dict(item)
        item_data["price"] = float(item_data["price"])
        order_data["items"].append(item_data)

    return order_data


def cancel_timeout_orders():
    timeout_minutes = 30
    with get_cursor() as cur:
        cur.execute(
            """SELECT id FROM orders
               WHERE status='pending' AND created_at < NOW() - INTERVAL '%s minutes'""",
            (timeout_minutes,),
        )
        timeout_ids = [row["id"] for row in cur.fetchall()]

    logger.info("[Scheduler] 发现 %d 个超时订单待取消", len(timeout_ids))
    for oid in timeout_ids:
        try:
            _cancel_timeout_order_by_id(oid)
            logger.info("[Scheduler] 订单 %s 已自动取消", oid)
        except Exception as e:
            logger.error("[Scheduler] 取消订单 %s 失败: %s", oid, str(e))


def _cancel_timeout_order_by_id(order_id):
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, status FROM orders WHERE id=%s FOR UPDATE", (order_id,))
        order = cur.fetchone()
        if not order or order["status"] != "pending":
            return

        cur.execute("SELECT product_id, quantity FROM order_items WHERE order_id=%s", (order_id,))
        items = cur.fetchall()
        for item in items:
            cur.execute(
                "UPDATE products SET stock = stock + %s WHERE id = %s",
                (item["quantity"], item["product_id"]),
            )
        cur.execute("UPDATE orders SET status='cancelled', cancelled_at=NOW() WHERE id=%s", (order_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)
