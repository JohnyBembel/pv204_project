from fastapi import APIRouter, HTTPException, status
from models.user import UserResponse
from services.user_service import user_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user():
    """
    Register a new user.

    The endpoint generates a Nostr key pair and returns both keys.
    Only the public key is saved to MongoDB.
    """
    try:
        new_user = await user_service.register_user()
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering user: {e}"
        )
