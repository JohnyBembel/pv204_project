from fastapi import Header, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from services.noise_auth_service import NoiseAuthService
from database import mongodb

noise_auth_service = NoiseAuthService()

async def get_current_user(x_noise_token: str = Header(...)) -> Dict[str, Any]:
    """
    Retrieve the current user using the Noise session token provided in the headers.
    The token is used to find a valid session stored in MongoDB, and the public key stored in that session is
    then used to get the corresponding user record from the database.
    """
    # Look up the Noise session in the database
    session = await mongodb.db.noise_sessions.find_one({"session_id": x_noise_token})
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    # Check if the session has expired
    if datetime.utcnow() > session.get("expires_at", datetime.min):
        # Remove expired session from DB
        await mongodb.db.noise_sessions.delete_one({"session_id": x_noise_token})
        raise HTTPException(
            status_code=401,
            detail="Session has expired"
        )

    # Retrieve the user using the public key obtained during the handshake.
    user = await mongodb.db.users.find_one({"nostr_public_key": session["public_key"]})
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Convert MongoDB's ObjectId into a string identifier if needed
    if "_id" in user:
        user["id"] = str(user["_id"])
        del user["_id"]

    return user
