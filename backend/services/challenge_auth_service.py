# services/challenge_auth_service.py
import uuid
from datetime import datetime, timedelta
from bech32 import bech32_decode, convertbits
import nacl.signing
import nacl.exceptions
import binascii

# In-memory session store (for simplicity)
SESSIONS = {}
SESSION_LIFETIME_SECONDS = 300  # 5 minutes


def parse_public_key(npub: str) -> bytes:
    """
    Decodes a Nostr public key in bech32 format (npub...) into its raw 32-byte value.
    """
    try:
        hrp, data = bech32_decode(npub)
        if data is None:
            raise ValueError("bech32_decode returned None")
        raw_pubkey = bytes(convertbits(data, 5, 8, False))
        if len(raw_pubkey) != 32:
            raise ValueError(f"Invalid public key length: {len(raw_pubkey)} (expected 32 bytes)")
        print(f"DEBUG: Parsed public key {npub} to raw hex: {raw_pubkey.hex()}")
        return raw_pubkey
    except Exception as e:
        print(f"DEBUG: Error in parse_public_key for {npub}: {e}")
        raise e


def get_public_key_from_seed(raw_seed_hex: str) -> bytes:
    """
    Generate the public key from a raw seed using the same method as TweetNaCl in the frontend.
    This helps us verify signatures created by TweetNaCl on the frontend.
    """
    try:
        raw_seed = binascii.unhexlify(raw_seed_hex)
        if len(raw_seed) != 32:
            raise ValueError(f"Invalid seed length: {len(raw_seed)} (expected 32 bytes)")

        # Create a signing key from the raw seed
        signing_key = nacl.signing.SigningKey(raw_seed)

        # Get the verify key (public key)
        verify_key = signing_key.verify_key

        # Get the raw bytes of the public key
        raw_pubkey = verify_key.encode()

        print(f"DEBUG: Generated public key from seed {raw_seed_hex[:8]}...: {raw_pubkey.hex()}")
        return raw_pubkey
    except Exception as e:
        print(f"DEBUG: Error generating public key from seed: {e}")
        raise e


class ChallengeAuthService:
    def get_challenge(self, public_key: str) -> (str, str):
        session_id = str(uuid.uuid4())
        challenge = f"auth-challenge:{session_id}"
        expires_at = datetime.utcnow() + timedelta(seconds=SESSION_LIFETIME_SECONDS)
        SESSIONS[session_id] = {
            "public_key": public_key,  # stored in bech32 format, e.g., "npub1..."
            "challenge": challenge,
            "expires_at": expires_at,
            "verified": False
        }
        print(
            f"DEBUG: Created challenge for public key {public_key} -> session_id: {session_id}, challenge: {challenge}")
        return session_id, challenge

    async def verify_challenge_signature(self, session_id: str, signature: bytes) -> bool:
        session_data = SESSIONS.get(session_id)
        if not session_data:
            print(f"DEBUG: Session {session_id} not found.")
            return False
        if datetime.utcnow() > session_data["expires_at"]:
            print(f"DEBUG: Session {session_id} expired.")
            del SESSIONS[session_id]
            return False

        stored_pubkey_bech32 = session_data["public_key"]
        challenge_str = session_data["challenge"]

        try:
            # Decode the stored public key using our helper
            raw_pubkey = parse_public_key(stored_pubkey_bech32)
            print(f"DEBUG: Using raw public key (hex): {raw_pubkey.hex()} for session {session_id}")

            # Encode the challenge
            challenge_bytes = challenge_str.encode()
            print(f"DEBUG: Challenge bytes: {challenge_bytes}")

            verify_key = nacl.signing.VerifyKey(raw_pubkey)
            # Attempt to verify the signature
            try:
                verify_key.verify(challenge_bytes, signature)
                session_data["verified"] = True
                print(f"DEBUG: Signature verification successful for session {session_id}")
                return True
            except nacl.exceptions.BadSignatureError:
                # If verification fails with the bech32-derived key, try using the user's raw seed
                # This is a fallback to handle TweetNaCl's key derivation on the frontend
                from database import mongodb
                user = None
                try:
                    # Use await here since find_one is an async operation
                    user = await mongodb.db.users.find_one({"nostr_public_key": stored_pubkey_bech32})
                except Exception as e:
                    print(f"DEBUG: Error finding user: {e}")

                if user and "raw_seed" in user:
                    try:
                        # Generate the public key using TweetNaCl's method
                        tweetnacl_pubkey = get_public_key_from_seed(user["raw_seed"])
                        print(f"DEBUG: TweetNaCl-derived public key: {tweetnacl_pubkey.hex()}")

                        # Verify with the TweetNaCl-derived public key
                        tweetnacl_verify_key = nacl.signing.VerifyKey(tweetnacl_pubkey)
                        tweetnacl_verify_key.verify(challenge_bytes, signature)

                        session_data["verified"] = True
                        print(f"DEBUG: Signature verification successful with TweetNaCl key for session {session_id}")
                        return True
                    except nacl.exceptions.BadSignatureError as bse:
                        print(f"DEBUG: TweetNaCl fallback verification also failed for session {session_id}: {bse}")
                        return False
                    except Exception as e:
                        print(f"DEBUG: Error in TweetNaCl fallback: {e}")
                        return False
                else:
                    print(f"DEBUG: No raw seed found for user with public key {stored_pubkey_bech32}")
                    return False
        except nacl.exceptions.BadSignatureError as bse:
            print(f"DEBUG: BadSignatureError for session {session_id}: {bse}")
            return False
        except Exception as e:
            print(f"DEBUG: Exception during verification for session {session_id}: {e}")
            return False

    def is_session_valid(self, session_id: str) -> bool:
        session_data = SESSIONS.get(session_id)
        if not session_data:
            return False
        if datetime.utcnow() > session_data["expires_at"]:
            del SESSIONS[session_id]
            return False
        return session_data["verified"]

    def get_public_key_for_session(self, session_id: str) -> str:
        session_data = SESSIONS.get(session_id)
        if not session_data:
            return None
        if datetime.utcnow() > session_data["expires_at"]:
            del SESSIONS[session_id]
            return None
        if not session_data["verified"]:
            return None
        return session_data["public_key"]


challenge_auth_service = ChallengeAuthService()