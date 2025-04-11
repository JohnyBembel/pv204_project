from pydantic import BaseModel
from datetime import datetime

class UserResponse(BaseModel):
    id: str
    nostr_public_key: str
    nostr_private_key: str
    created_at: datetime
