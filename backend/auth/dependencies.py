# auth/dependencies.py
from fastapi import Header, HTTPException
from typing import Dict, Any
from services.challenge_auth_service import challenge_auth_service
from database import mongodb

async def get_current_user(x_noise_token: str = Header(...)) -> Dict[str, Any]:
    if not challenge_auth_service.is_session_valid(x_noise_token):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    pubkey = challenge_auth_service.get_public_key_for_session(x_noise_token)
    if not pubkey:
        raise HTTPException(status_code=401, detail="Session not verified or expired")
    user = await mongodb.db.users.find_one({"nostr_public_key": pubkey})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "_id" in user:
        user["id"] = str(user["_id"])
        del user["_id"]
    return user
