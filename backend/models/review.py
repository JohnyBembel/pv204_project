from pydantic import BaseModel

class ReviewCreate(BaseModel):
    transaction_id: str
    rating: int
    comment: str

class ReviewResponse(BaseModel):
    transaction_id: str
    seller_pubkey: str
    rating: int
    comment: str
    verified: bool