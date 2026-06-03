from pydantic import BaseModel


class CreateOrderRequest(BaseModel):
    address: str
