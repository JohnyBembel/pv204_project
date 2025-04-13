from pydantic import BaseModel
from datetime import datetime

class UserResponse(BaseModel):
    id: str
    nostr_public_key: str
    nostr_private_key: str
    raw_seed: str
    created_at: datetime
    lightning_address: str