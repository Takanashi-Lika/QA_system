from pydantic import BaseModel
from typing import Optional


class CreateCategoryRequest(BaseModel):
    name: str
    parent_id: Optional[int] = None


class UpdateCategoryRequest(BaseModel):
    name: str
