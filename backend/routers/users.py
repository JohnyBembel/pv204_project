from fastapi import APIRouter, HTTPException, status
from models.user import UserResponse
from services.user_service import user_service
from pydantic import BaseModel

# body schema for la
class RegisterRequest(BaseModel):
    lightning_address: str

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: RegisterRequest):
    """
    Register a new user.

    The endpoint generates a Nostr key pair and returns both keys.
    Only the public key is saved to MongoDB.
    """
    try:
        new_user = await user_service.register_user(lightning_address=request.lightning_address)
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering user: {e}"
        )
