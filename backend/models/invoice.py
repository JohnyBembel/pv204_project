from decimal import Decimal

from pydantic import BaseModel
from datetime import datetime

class Invoice(BaseModel):
    type: str
    invoice: str
    description: str
    payment_hash: str
    amount: int
    fees_paid: int
    created_at: int