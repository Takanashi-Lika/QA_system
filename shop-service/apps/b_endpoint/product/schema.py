from pydantic import BaseModel
from typing import Optional


class CreateProductRequest(BaseModel):
    name: str
    description: str = ""
    price: float
    image_url: str = ""
    stock: int
    category_id: int


class UpdateProductRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
