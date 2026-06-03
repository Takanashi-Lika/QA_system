from fastapi import APIRouter, Depends

from apps.common.auth import get_current_admin
from apps.b_endpoint.product.schema import CreateProductRequest, UpdateProductRequest
from domain.product.product_service import (
    create_product,
    update_product,
    toggle_product_status,
)

router = APIRouter(
    prefix="/b-endpoint/products",
    tags=["B端-商品"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("/")
def publish_product(req: CreateProductRequest, admin: dict = Depends(get_current_admin)):
    product = create_product(
        name=req.name,
        description=req.description,
        price=req.price,
        image_url=req.image_url,
        stock=req.stock,
        category_id=req.category_id,
    )
    return {"code": 0, "message": "ok", "data": product}


@router.put("/{product_id}")
def edit_product(product_id: int, req: UpdateProductRequest, admin: dict = Depends(get_current_admin)):
    product = update_product(product_id, **req.model_dump())
    return {"code": 0, "message": "ok", "data": product}


@router.patch("/{product_id}/status")
def toggle_status(product_id: int, admin: dict = Depends(get_current_admin)):
    product = toggle_product_status(product_id)
    return {"code": 0, "message": "ok", "data": product}
