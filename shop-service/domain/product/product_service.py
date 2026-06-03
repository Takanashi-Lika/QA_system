from infrastructure.database import get_cursor
from infrastructure.redis_client import get_cache, set_cache, delete_cache, delete_keys, CacheLocks
from common.exceptions import NotFoundError, ValidationError


def _get_child_category_ids(category_id):
    ids = [category_id]
    with get_cursor() as cur:
        cur.execute("SELECT id FROM categories WHERE parent_id = %s", (category_id,))
        children = cur.fetchall()
        for child in children:
            ids.extend(_get_child_category_ids(child["id"]))
    return ids


def get_hot_products():
    cached = get_cache("hot:products:list")
    if cached is not None:
        return cached

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT p.id, p.name, p.description, p.price, p.image_url, p.stock,
                   p.category_id, c.name AS category_name, p.status, p.created_at, p.updated_at
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'on_sale'
            ORDER BY p.created_at DESC
            LIMIT 5
            """
        )
        rows = cur.fetchall()

    result = [dict(row) for row in rows]
    set_cache("hot:products:list", result, ttl=300)
    return result


def get_products_by_category(category_id, page=1, size=20):
    category_ids = _get_child_category_ids(category_id)
    offset = (page - 1) * size

    with get_cursor() as cur:
        cur.execute(
            "SELECT count(*) AS total FROM products WHERE category_id = ANY(%s) AND status = 'on_sale'",
            (category_ids,),
        )
        total = cur.fetchone()["total"]

        cur.execute(
            """
            SELECT p.id, p.name, p.description, p.price, p.image_url, p.stock,
                   p.category_id, c.name AS category_name, p.status, p.created_at, p.updated_at
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.category_id = ANY(%s) AND p.status = 'on_sale'
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (category_ids, size, offset),
        )
        rows = cur.fetchall()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [dict(row) for row in rows],
    }


def search_products(keyword, page=1, size=20):
    offset = (page - 1) * size
    like_pattern = f"%{keyword}%"

    with get_cursor() as cur:
        cur.execute(
            "SELECT count(*) AS total FROM products WHERE name ILIKE %s AND status = 'on_sale'",
            (like_pattern,),
        )
        total = cur.fetchone()["total"]

        cur.execute(
            """
            SELECT p.id, p.name, p.description, p.price, p.image_url, p.stock,
                   p.category_id, c.name AS category_name, p.status, p.created_at, p.updated_at
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.name ILIKE %s AND p.status = 'on_sale'
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (like_pattern, size, offset),
        )
        rows = cur.fetchall()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [dict(row) for row in rows],
    }


def get_product_detail(product_id):
    cache_key = f"product:{product_id}"

    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    lock = CacheLocks.acquire(cache_key)
    with lock:
        cached = get_cache(cache_key)
        if cached is not None:
            return cached

        with get_cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.name, p.description, p.price, p.image_url, p.stock,
                       p.category_id, c.name AS category_name, p.status, p.created_at, p.updated_at
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = %s AND p.status = 'on_sale'
                """,
                (product_id,),
            )
            row = cur.fetchone()

        if row is None:
            raise NotFoundError("商品不存在或已下架")

        result = dict(row)
        set_cache(cache_key, result, ttl=600)
        return result


def create_product(name, description, price, image_url, stock, category_id):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if cur.fetchone() is None:
            raise ValidationError("所属分类不存在")

        cur.execute(
            """
            INSERT INTO products (name, description, price, image_url, stock, category_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'on_sale')
            RETURNING id, name, description, price, image_url, stock, category_id, status, created_at, updated_at
            """,
            (name, description, price, image_url, stock, category_id),
        )
        row = cur.fetchone()

    delete_cache("hot:products:list")
    return dict(row)


def update_product(product_id, **fields):
    if not fields:
        raise ValidationError("至少需要提供一个更新字段")

    allowed_fields = {"name", "description", "price", "image_url", "stock", "category_id"}
    update_data = {k: v for k, v in fields.items() if k in allowed_fields and v is not None}
    if not update_data:
        raise ValidationError("没有有效的更新字段")

    if "category_id" in update_data:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE id = %s", (update_data["category_id"],))
            if cur.fetchone() is None:
                raise ValidationError("所属分类不存在")

    set_clause = ", ".join(f"{k} = %s" for k in update_data)
    values = list(update_data.values()) + [product_id]

    with get_cursor() as cur:
        cur.execute(
            f"""
            UPDATE products SET {set_clause}
            WHERE id = %s
            RETURNING id, name, description, price, image_url, stock, category_id, status, created_at, updated_at
            """,
            values,
        )
        row = cur.fetchone()

    if row is None:
        raise NotFoundError("商品不存在")

    delete_keys(f"product:{product_id}", "hot:products:list")
    return dict(row)


def toggle_product_status(product_id):
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE products
            SET status = CASE WHEN status = 'on_sale' THEN 'off_sale' ELSE 'on_sale' END
            WHERE id = %s
            RETURNING id, name, description, price, image_url, stock, category_id, status, created_at, updated_at
            """,
            (product_id,),
        )
        row = cur.fetchone()

    if row is None:
        raise NotFoundError("商品不存在")

    delete_keys(f"product:{product_id}", "hot:products:list")
    return dict(row)
