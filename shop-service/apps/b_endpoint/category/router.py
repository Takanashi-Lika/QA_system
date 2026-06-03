from fastapi import APIRouter, Depends

from apps.b_endpoint.category.schema import CreateCategoryRequest, UpdateCategoryRequest
from apps.common.auth import get_current_admin
from domain.category.category_service import (
    create_category,
    delete_category,
    get_category_tree,
    update_category,
)

router = APIRouter(prefix="/b-endpoint/categories", tags=["B端-分类管理"])


@router.get("/")
def list_categories():
    tree = get_category_tree()
    return {"code": 0, "data": tree, "message": "success"}


@router.post("/")
def create_category_api(body: CreateCategoryRequest, _user: dict = Depends(get_current_admin)):
    category = create_category(name=body.name, parent_id=body.parent_id)
    return {"code": 0, "data": category, "message": "success"}


@router.put("/{category_id}")
def update_category_api(category_id: int, body: UpdateCategoryRequest, _user: dict = Depends(get_current_admin)):
    category = update_category(category_id=category_id, name=body.name)
    return {"code": 0, "data": category, "message": "success"}


@router.delete("/{category_id}")
def delete_category_api(category_id: int, _user: dict = Depends(get_current_admin)):
    delete_category(category_id=category_id)
    return {"code": 0, "data": None, "message": "success"}
