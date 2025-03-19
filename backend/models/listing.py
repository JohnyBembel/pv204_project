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


class ShippingOption(str, Enum):
    STANDARD = "standard"
    EXPEDITED = "expedited"
    ONE_DAY = "one_day"
    PICKUP_ONLY = "pickup_only"
    FREE = "free"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    ENDED = "ended"
    DRAFT = "draft"


class Category(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None


class Image(BaseModel):
    url: HttpUrl
    is_primary: bool = False
    description: Optional[str] = None


class Address(BaseModel):
    city: str
    state: str
    country: str
    postal_code: str
    street_address: Optional[str] = None


class SellerInfo(BaseModel):
    id: UUID
    username: str
    rating: float = Field(ge=0, le=5)
    reviews_count: int = 0
    joined_date: datetime
    location: Optional[Address] = None


class BidInfo(BaseModel):
    current_price: float = Field(gt=0)
    bid_count: int = 0
    highest_bidder_id: Optional[UUID] = None
    start_time: datetime
    end_time: datetime


class ListingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: str = Field(..., min_length=20, max_length=5000)
    condition: ListingCondition
    category_id: int
    price: float = Field(gt=0)
    quantity: int = Field(ge=1, default=1)
    is_auction: bool = False
    shipping_options: List[ShippingOption] = [ShippingOption.STANDARD]
    shipping_price: float = Field(ge=0)
    location: Address
    tags: List[str] = []

    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v


class ListingCreate(ListingBase):
    images: List[HttpUrl] = Field(..., min_items=1, max_items=12)


class ListingInDB(ListingBase):
    id: UUID = Field(default_factory=uuid4)
    seller_id: UUID
    images: List[Image]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: ListingStatus = ListingStatus.ACTIVE
    views_count: int = 0
    favorite_count: int = 0
    category: Optional[Category] = None
    seller: Optional[SellerInfo] = None
    bid_info: Optional[BidInfo] = None
    nostr_event_id: Optional[str] = None  # Store Nostr event ID

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
    shipping_options: Optional[List[ShippingOption]] = None
    shipping_price: Optional[float] = Field(None, ge=0)
    status: Optional[ListingStatus] = None
    tags: Optional[List[str]] = None

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v


class ListingSearchParams(BaseModel):
    keyword: Optional[str] = None
    category_id: Optional[int] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, gt=0)
    condition: Optional[ListingCondition] = None
    seller_id: Optional[UUID] = None
    is_auction: Optional[bool] = None
    status: Optional[ListingStatus] = ListingStatus.ACTIVE
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    limit: int = 20
    offset: int = 0