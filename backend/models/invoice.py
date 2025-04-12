from decimal import Decimal

from pydantic import BaseModel
from datetime import datetime

class Invoice(BaseModel):
    amnt: Decimal
    desc: str