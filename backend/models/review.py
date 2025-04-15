from pydantic import BaseModel

class ProofOfPurchase(BaseModel):
    transaction_id: str
    listing_id: str
    buyer_pubkey: str
    seller_pubkey: str
    seller_signature: str  # signature from the seller
    