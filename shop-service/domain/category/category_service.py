from infrastructure.database import get_cursor
from common.exceptions import BusinessError, NotFoundError
from infrastructure.redis_client import get_cache, set_cache, delete_cache

CACHE_KEY = "categories:tree"
CACHE_TTL = 1800


def get_category_tree() -> list[dict]:
    cached = get_cache(CACHE_KEY)
    if cached is not None:
        return cached

    with get_cursor() as cursor:
        cursor.execute("SELECT id, name, parent_id FROM categories ORDER BY id")
        rows = cursor.fetchall()

    children_map: dict[int, list[dict]] = {}
    roots: list[dict] = []

    for row in rows:
        item = {"id": row["id"], "name": row["name"], "parent_id": row["parent_id"], "children": []}
        if row["parent_id"] is None:
            roots.append(item)
        else:
            children_map.setdefault(row["parent_id"], []).append(item)

    for root in roots:
        root["children"] = children_map.get(root["id"], [])

    set_cache(CACHE_KEY, roots, CACHE_TTL)
    return roots


def create_category(name: str, parent_id: int | None = None) -> dict:
    with get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO categories (name, parent_id) VALUES (%s, %s) RETURNING id, name, parent_id",
            (name, parent_id),
        )
        row = cursor.fetchone()
    delete_cache(CACHE_KEY)
    return dict(row)


def update_category(category_id: int, name: str) -> dict:
    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE categories SET name = %s WHERE id = %s RETURNING id, name, parent_id",
            (name, category_id),
        )
        row = cursor.fetchone()
    if row is None:
        raise NotFoundError("分类不存在")
    delete_cache(CACHE_KEY)
    return dict(row)


def delete_category(category_id: int) -> None:
    with get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM products WHERE category_id = %s", (category_id,))
        count = cursor.fetchone()["cnt"]
        if count > 0:
            raise BusinessError(f"该分类下存在 {count} 个商品，无法删除")

        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        if cursor.rowcount == 0:
            raise NotFoundError("分类不存在")

    delete_cache(CACHE_KEY)
