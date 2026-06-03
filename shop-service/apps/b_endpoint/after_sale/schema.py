from pydantic import BaseModel


class ReviewAfterSaleRequest(BaseModel):
    action: str
