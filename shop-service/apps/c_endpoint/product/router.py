from fastapi import APIRouter, Query

from domain.product.product_service import (
    get_hot_products,
    get_products_by_category,
    search_products,
    get_product_detail,
)

router = APIRouter(prefix="/c-endpoint", tags=["C端-商品"])


@router.get("/products/hot")
def hot_products():
    return {"code": 0, "message": "ok", "data": get_hot_products()}


@router.get("/products")
def list_products(
    category_id: int = Query(None),
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    if keyword:
        result = search_products(keyword, page, size)
    elif category_id:
        result = get_products_by_category(category_id, page, size)
    else:
        result = get_hot_products()
    return {"code": 0, "message": "ok", "data": result}


@router.get("/products/{product_id}")
def product_detail(product_id: int):
    return {"code": 0, "message": "ok", "data": get_product_detail(product_id)}
