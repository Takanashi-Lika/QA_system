from infrastructure.database import get_cursor
from common.exceptions import NotFoundError, BusinessError


def add_to_cart(user_id, product_id, quantity):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, name, stock, status FROM products WHERE id = %s",
            (product_id,),
        )
        product = cur.fetchone()
        if product is None or product["status"] != "on_sale":
            raise BusinessError("商品已下架，无法添加")
        if quantity > product["stock"]:
            raise BusinessError("超出商品库存")

        cur.execute(
            """
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id)
            DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
            RETURNING id, user_id, product_id, quantity, created_at
            """,
            (user_id, product_id, quantity),
        )
        row = cur.fetchone()

    return dict(row)


def update_cart_item(user_id, product_id, quantity):
    if quantity <= 0:
        raise BusinessError("数量必须大于0")

    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE cart_items
            SET quantity = %s
            WHERE user_id = %s AND product_id = %s
            RETURNING id, user_id, product_id, quantity, created_at
            """,
            (quantity, user_id, product_id),
        )
        row = cur.fetchone()

    if row is None:
        raise NotFoundError("购物车项不存在")

    return dict(row)


def remove_from_cart(user_id, product_id):
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s",
            (user_id, product_id),
        )


def get_cart(user_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT ci.id, ci.user_id, ci.product_id, ci.quantity, ci.created_at, ci.updated_at,
                   p.name AS product_name, p.price, p.stock, p.status
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s
            ORDER BY ci.created_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    items = [dict(row) for row in rows]
    total_amount = round(sum(item["price"] * item["quantity"] for item in items), 2)

    return {
        "items": items,
        "total_amount": total_amount,
    }
