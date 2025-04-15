# auth/dependencies.py
from fastapi import Header, HTTPException, Query
from typing import Dict, Any
from services.challenge_auth_service import challenge_auth_service
from database import mongodb


async def get_current_user(token: str = Query(..., alias="session-token")):
    """
    This dependency validates the session token and gets the associated user.
    It can be used in other route handlers that require authentication.
    """
    is_valid = await challenge_auth_service.is_session_valid(token)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Get the public key from the session
    public_key = await challenge_auth_service.get_public_key_for_session(token)
    if not public_key:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Fetch the user from the database using the public key
    from database import mongodb
    user = await mongodb.db.users.find_one({"nostr_public_key": public_key})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Return user data for use in protected routes
    return user