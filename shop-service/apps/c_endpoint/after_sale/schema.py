from pydantic import BaseModel


class CreateAfterSaleRequest(BaseModel):
    order_id: int
    type: str
    reason: str
