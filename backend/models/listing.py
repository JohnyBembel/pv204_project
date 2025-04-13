from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ListingCondition(str, Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    VERY_GOOD = "very_good"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    FOR_PARTS = "for_parts"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"


class Image(BaseModel):
    url: HttpUrl
    is_primary: bool = False
    description: Optional[str] = None


class SellerInfo(BaseModel):
    nostr_public_key: str
    name: Optional[str] = None
    about: Optional[str] = None
    picture: Optional[str] = None

    @validator('nostr_public_key')
    def check_pubkey(cls, v):
        if not v.startswith("npub"):
            raise ValueError("Invalid Nostr public key (should start with 'npub')")
        return v

class ListingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: str = Field(..., min_length=20, max_length=5000)
    condition: ListingCondition
    category_id: int
    price: float = Field(gt=0)
    quantity: int = Field(ge=1, default=1)
    shipping_price: float = Field(ge=0)
    tags: List[str] = []

    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v


class ListingCreate(ListingBase):
    images: List[HttpUrl] = Field(..., min_items=1, max_items=12)


class ListingInDB(ListingBase):
    id: UUID
    seller_id: UUID
    images: List[Image]
    created_at: datetime
    updated_at: datetime
    status: ListingStatus = ListingStatus.ACTIVE
    views_count: int = 0
    favorite_count: int = 0
    category: str
    seller: Optional[SellerInfo] = None
    nostr_event_id: Optional[str] = None

    class Config:
        orm_mode = True


class ListingResponse(ListingInDB):
    pass


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=80)
    description: Optional[str] = Field(None, min_length=20, max_length=5000)
    condition: Optional[ListingCondition] = None
    category_id: Optional[int] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=1)
    status: Optional[ListingStatus] = None
    tags: Optional[List[str]] = None

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v