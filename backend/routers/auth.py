from fastapi import APIRouter, HTTPException, Query, Depends, Header
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
    session_id, challenge = await challenge_auth_service.get_challenge(public_key)
    return {"session_id": session_id, "challenge": challenge}


@router.post("/verify", response_model=VerifyResponse)
async def verify_signature(req: VerifyRequest):
    try:
        signature_bytes = base64.b64decode(req.signature_b64)

        # Verify the signature with the challenge
        is_valid = await challenge_auth_service.verify_challenge_signature(req.session_id, signature_bytes)

        if not is_valid:
            return {"authenticated": False, "token": None}
        return {"authenticated": True, "token": req.session_id}
    except Exception as e:
        return {"authenticated": False, "token": None}


@router.get("/validate")
async def validate_token(
        token: str = Query(None, alias="session-token"),
        token_header: str = Header(None, alias="session-token"),
        authorization: str = Header(None)
):
    """Validates if a token is still valid"""
    # Try to get the token from various sources
    actual_token = token or token_header or None

    # Check if token is in Authorization header
    if authorization and not actual_token:
        if authorization.startswith("Bearer "):
            actual_token = authorization.replace("Bearer ", "")

    if not actual_token:
        raise HTTPException(status_code=422, detail="Token is required")

    is_valid = await challenge_auth_service.is_session_valid(actual_token)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"valid": True}