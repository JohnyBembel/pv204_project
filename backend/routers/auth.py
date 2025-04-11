from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional
import base64
from datetime import datetime
import json

from services.noise_auth_service import NoiseAuthService
from database import mongodb

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

noise_auth_service = NoiseAuthService()


# Request/response models
class HandshakeInitRequest(BaseModel):
    public_key: str  # Nostr public key in hex format


class HandshakeInitResponse(BaseModel):
    session_id: str
    message: str  # Base64 encoded message


class HandshakeCompleteRequest(BaseModel):
    session_id: str
    message: str  # Base64 encoded message


class HandshakeCompleteResponse(BaseModel):
    success: bool
    message: Optional[str] = None  # Base64 encoded message or error message


class SignedChallengeRequest(BaseModel):
    session_id: str
    signature: str  # Base64 encoded signature of the challenge


class SignedChallengeResponse(BaseModel):
    authenticated: bool
    token: Optional[str] = None


@router.post("/noise/initiate", response_model=HandshakeInitResponse)
async def initiate_handshake(request: HandshakeInitRequest, background_tasks: BackgroundTasks):
    """
    Initiate a Noise Protocol handshake
    """
    try:
        # Clean expired sessions in background
        background_tasks.add_task(noise_auth_service.clean_expired_sessions)

        # Verify the public key exists in the database
        user = await mongodb.db.users.find_one({"nostr_public_key": request.public_key})
        if not user:
            raise HTTPException(status_code=404, detail="User with this public key not found")

        # Initiate handshake
        session_id, message = noise_auth_service.initiate_handshake(request.public_key)

        # Return session ID and base64-encoded message
        return HandshakeInitResponse(
            session_id=session_id,
            message=base64.b64encode(message).decode('ascii')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating handshake: {str(e)}")


@router.post("/noise/complete", response_model=HandshakeCompleteResponse)
async def complete_handshake(request: HandshakeCompleteRequest):
    """
    Complete a Noise Protocol handshake
    """
    try:
        # Decode the client message
        client_message = base64.b64decode(request.message)

        # Process the client message
        success, response_message = noise_auth_service.complete_handshake(
            request.session_id,
            client_message
        )

        if not success:
            return HandshakeCompleteResponse(
                success=False,
                message="Handshake failed"
            )

        # Store the session information in the database for later reference
        await mongodb.db.noise_sessions.insert_one({
            "session_id": request.session_id,
            "public_key": noise_auth_service.active_sessions[request.session_id]["pubkey"],
            "created_at": datetime.utcnow(),
            "expires_at": noise_auth_service.active_sessions[request.session_id]["expires_at"]
        })

        # Return success
        return HandshakeCompleteResponse(
            success=True,
            message="Handshake completed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing handshake: {str(e)}")


@router.post("/noise/verify", response_model=SignedChallengeResponse)
async def verify_signature(request: SignedChallengeRequest):
    """
    Verify a signature of a challenge to authenticate a user
    """
    try:
        # Decode the signature
        signature = base64.b64decode(request.signature)

        # Verify the signature
        is_valid = noise_auth_service.verify_user_ownership(
            request.session_id,
            signature
        )

        if not is_valid:
            return SignedChallengeResponse(
                authenticated=False
            )

        # Generate a token or session for the authenticated user
        # For this example, we'll just use the session_id as the token
        # In a real application, you might want to use JWT or another token format

        return SignedChallengeResponse(
            authenticated=True,
            token=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying signature: {str(e)}")