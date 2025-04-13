from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import base64
from typing import Optional
from services.challenge_auth_service import challenge_auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])


class ChallengeResponse(BaseModel):
    session_id: str
    challenge: str


class VerifyRequest(BaseModel):
    session_id: str
    signature_b64: str  # Base64-encoded signature


class VerifyResponse(BaseModel):
    authenticated: bool
    token: Optional[str] = None


@router.get("/challenge", response_model=ChallengeResponse)
async def get_challenge(public_key: str = Query(...)):
    session_id, challenge = challenge_auth_service.get_challenge(public_key)
    return {"session_id": session_id, "challenge": challenge}


@router.post("/verify", response_model=VerifyResponse)
async def verify_signature(req: VerifyRequest):
    try:
        print(f"DEBUG: Incoming request body: {req.dict()}")
        signature_bytes = base64.b64decode(req.signature_b64)

        # Make sure to await the async verification
        is_valid = await challenge_auth_service.verify_challenge_signature(req.session_id, signature_bytes)

        if not is_valid:
            return {"authenticated": False, "token": None}
        return {"authenticated": True, "token": req.session_id}
    except Exception as e:
        print(f"DEBUG: Exception in verify_signature endpoint: {e}")
        return {"authenticated": False, "token": None}