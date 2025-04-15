from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    pass
class UserCreate(UserBase):
    pass

class UserResponse(BaseModel):
    id: str
    nostr_public_key: str
    created_at: datetime
    nostr_private_key: Optional[str] = None
    raw_seed: Optional[str] = None

    class Config:
        orm_mode = True

class UserProfileResponse(BaseModel):
    id: str
    nostr_public_key: str
    lightning_address: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True