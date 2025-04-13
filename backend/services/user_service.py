from uuid import uuid4
from datetime import datetime
from nostr_sdk import Keys
from database import mongodb  # Ensure your MongoDB connection is set up
from bech32 import bech32_decode, convertbits

class UserService:
    collection_name = "users"

    def generate_nostr_key_pair(self, prefix: str):
        """
        Generate a Nostr key pair repeatedly until the public key starts with the given prefix.
        Returns a tuple: (private_key, public_key).
        Both keys are nostr_sdk.Key objects; you can call .to_bech32() on them.
        """
        while True:
            keys = Keys.generate()
            private_key = keys.secret_key()
            public_key = keys.public_key()
            bech32_pub = public_key.to_bech32()
            print(f"Generated Public Key: {bech32_pub}")
            print(f"Generated Private Key: {private_key.to_bech32()}")
            if bech32_pub.startswith(prefix):
                print(f"Public key starts with '{prefix}'")
                return private_key, public_key

    def derive_raw_seed_from_private_key(self, private_key: str) -> str:
        """Extract raw seed bytes from a private key and return as hex string"""

        hrp, data = bech32_decode(private_key)
        if not data:
            raise ValueError("Invalid private key format")
        raw_seed_bytes = bytes(convertbits(data, 5, 8, False))
        return raw_seed_bytes.hex()

    async def register_user(self, lightning_address: str) -> dict:
        """
        Register a new user by generating a Nostr key pair using the forced prefix.
        Only the public key is stored in the database.
        Returns a dict containing user id, public key, private key, creation timestamp,
        and the provided lightning_address.
        """
        prefix = "npub1mrkt"
        private_key, public_key = self.generate_nostr_key_pair(prefix)
        user_id = uuid4()
        created_at = datetime.utcnow()

        user_record = {
            "id": str(user_id),
            "nostr_public_key": public_key.to_bech32(),
            "created_at": created_at,
            "lightning_address": lightning_address,
        }
        user_record["_id"] = str(user_id)

        collection = mongodb.db[self.collection_name]
        result = await collection.insert_one(user_record)
        print(f"Inserted user with id: {result.inserted_id}")

        response = {
            "id": str(user_id),
            "nostr_public_key": public_key.to_bech32(),
            "nostr_private_key": private_key.to_bech32(),  # Returned for testing/demo
            "created_at": created_at,
            "lightning_address": lightning_address,
        }
        return response

    async def login_user(self, private_key: str) -> dict:
        """
        Log in a user based on their private key (nsec1...).
        Uses nostr-sdk to parse the provided private key (nsec1 string),
        derives the public key and checks that it starts with "npub1mrkt".
        If the user exists in the database, returns the user.
        Otherwise, creates a new user with the derived public key.
        """
        # Parse the provided private key (nsec1 string)
        try:
            keys = Keys.parse(private_key)
        except Exception as e:
            raise ValueError("Unable to parse private key. Ensure it is a valid nsec1 string.") from e

        derived_public_key = keys.public_key().to_bech32()
        prefix = "npub1mrkt"
        if not derived_public_key.startswith(prefix):
            raise ValueError("Derived public key does not meet required prefix (mrkt).")

        collection = mongodb.db[self.collection_name]
        user = await collection.find_one({"nostr_public_key": derived_public_key})
        if user:
            print("DEBUG (Login): User exists. Logging in.")
        else:
            print("DEBUG (Login): User not found. Creating new user.")
            user_id = uuid4()
            created_at = datetime.utcnow()
            user_record = {
                "id": str(user_id),
                "nostr_public_key": derived_public_key,
                "created_at": created_at,
                "lightning_address": ""
            }
            user_record["_id"] = str(user_id)
            result = await collection.insert_one(user_record)
            user = user_record
            print(f"DEBUG (Login): Inserted new user with id: {result.inserted_id}")

        return {
            "id": user["id"],
            "nostr_public_key": user["nostr_public_key"],
            "lightning_address": user.get("lightning_address", ""),
            "created_at": user["created_at"]
        }


user_service = UserService()
