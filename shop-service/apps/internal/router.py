from fastapi import APIRouter, Depends, Query

from apps.common.auth import verify_internal_token
from infrastructure.database import get_cursor
from common.exceptions import NotFoundError

router = APIRouter(
    prefix="/internal",
    tags=["内部查询"],
    dependencies=[Depends(verify_internal_token)],
)


@router.get("/orders")
def list_orders(
    user_id: int = Query(..., description="用户ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * size
    with get_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) as total FROM orders WHERE user_id = %s",
            (user_id,),
        )
        total = cur.fetchone()["total"]

        cur.execute(
            "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (user_id, size, offset),
        )
        items = [dict(row) for row in cur.fetchall()]

    return {
        "code": 0,
        "data": {"items": items, "total": total, "page": page, "size": size},
        "message": "success",
    }


@router.get("/orders/{order_id}")
def get_order(order_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        if order is None:
            raise NotFoundError("订单不存在")

        cur.execute(
            "SELECT * FROM order_items WHERE order_id = %s",
            (order_id,),
        )
        items = [dict(row) for row in cur.fetchall()]

    return {
        "code": 0,
        "data": {**dict(order), "items": items},
        "message": "success",
    }


@router.get("/logistics")
def list_logistics(user_id: int = Query(..., description="用户ID")):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT lr.*
            FROM logistics_records lr
            JOIN orders o ON lr.order_id = o.id
            WHERE o.user_id = %s
            ORDER BY lr.created_at DESC
            """,
            (user_id,),
        )
        items = [dict(row) for row in cur.fetchall()]

    return {
        "code": 0,
        "data": {"items": items},
        "message": "success",
    }


@router.get("/after-sales")
def list_after_sales(user_id: int = Query(..., description="用户ID")):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM after_sale_requests WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        items = [dict(row) for row in cur.fetchall()]

    return {
        "code": 0,
        "data": {"items": items},
        "message": "success",
    }


@router.get("/products/search")
def search_products(
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * size
    pattern = f"%{keyword}%"
    with get_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) as total FROM products WHERE name ILIKE %s AND status = 'on_sale'",
            (pattern,),
        )
        total = cur.fetchone()["total"]

        cur.execute(
            "SELECT * FROM products WHERE name ILIKE %s AND status = 'on_sale' ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (pattern, size, offset),
        )
        items = [dict(row) for row in cur.fetchall()]

    return {
        "code": 0,
        "data": {"items": items, "total": total, "page": page, "size": size},
        "message": "success",
    }


@router.get("/products/{product_id}")
def get_product(product_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        if product is None:
            raise NotFoundError("商品不存在")

    return {
        "code": 0,
        "data": dict(product),
        "message": "success",
    }


@router.get("/users/{user_id}")
def get_user(user_id: int):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, nickname, role, address, created_at, updated_at FROM users WHERE id = %s",
            (user_id,),
        )
        user = cur.fetchone()
        if user is None:
            raise NotFoundError("用户不存在")

    return {
        "code": 0,
        "data": dict(user),
        "message": "success",
    }
