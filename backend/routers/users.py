from fastapi import APIRouter, HTTPException, status, Query, Depends
from nostr_sdk import Keys

from auth.dependencies import get_current_user
from models.user import UserResponse, UserProfileResponse
from services.user_service import user_service
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    lightning_address: str


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: RegisterRequest):
    try:
        new_user = await user_service.register_user(lightning_address=request.lightning_address)
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering user: {e}"
        )


class LoginRequest(BaseModel):
    private_key: str


@router.post("/login", response_model=UserResponse)
async def login_user(request: LoginRequest):
    try:
        user = await user_service.login_user(private_key=request.private_key)

        # Extract the raw seed from the private key
        try:
            raw_seed = user_service.derive_raw_seed_from_private_key(request.private_key)
        except Exception as e:
            print(f"Error extracting raw seed: {e}")

        return {
            "id": user["id"],
            "nostr_public_key": user["nostr_public_key"],
            "lightning_address": user.get("lightning_address", ""),  # This should be a string
            "created_at": user["created_at"],
            "nostr_private_key": request.private_key,
            "raw_seed": raw_seed  # Provide a non-None value
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login failed: {e}"
        )

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(user: dict = Depends(get_current_user)):
    """Returns the profile of the authenticated user"""
    # user is the MongoDB document from the dependency
    return user