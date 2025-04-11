from noise.connection import NoiseConnection
import socket
import base64
from typing import Tuple, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from nostr_sdk import Keys

class NoiseAuthService:
    """
    Service for handling Noise Protocol authentication with Nostr public keys.
    """
    active_sessions = {}  # In-memory store for ongoing handshakes
    SESSION_EXPIRY = 300  # 5 minutes

    def __init__(self):
        pass

    def initiate_handshake(self, client_pubkey: str) -> Tuple[str, bytes]:
        # Generates a unique session and starts the handshake
        session_id = str(uuid4())
        noise = NoiseConnection.from_name(b'Noise_NN_25519_ChaChaPoly_SHA256')
        noise.set_as_initiator()
        noise.start_handshake()
        message = noise.write_message()
        expiry_time = datetime.utcnow() + timedelta(seconds=self.SESSION_EXPIRY)
        self.active_sessions[session_id] = {
            "noise": noise,
            "pubkey": client_pubkey,
            "expires_at": expiry_time,
            "completed": False
        }
        return session_id, message

    def complete_handshake(self, session_id: str, client_message: bytes) -> Tuple[bool, Optional[bytes]]:
        # Completes the handshake process
        if session_id not in self.active_sessions:
            return False, None

        session_data = self.active_sessions[session_id]
        if datetime.utcnow() > session_data["expires_at"]:
            del self.active_sessions[session_id]
            return False, None

        noise = session_data["noise"]
        noise.read_message(client_message)
        if noise.handshake_finished:
            session_data["completed"] = True
            return True, None
        else:
            next_message = noise.write_message()
            return False, next_message

    def verify_user_ownership(self, session_id: str, signed_challenge: bytes) -> bool:
        """
        Verify that the client owns the private key corresponding to the stored public key.
        The method compares a signature over a challenge using the public key.
        """
        if session_id not in self.active_sessions:
            return False
        session_data = self.active_sessions[session_id]
        pubkey = session_data["pubkey"]
        try:
            keys = Keys.from_public_key(pubkey)
            challenge = f"auth-challenge:{session_id}".encode()
            is_valid = keys.verify(challenge, signed_challenge)
            return is_valid
        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False

    def clean_expired_sessions(self):
        current_time = datetime.utcnow()
        expired_sessions = [
            sid for sid, data in self.active_sessions.items()
            if current_time > data["expires_at"]
        ]
        for sid in expired_sessions:
            del self.active_sessions[sid]

    def close_session(self, session_id: str) -> bool:
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
