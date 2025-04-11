from uuid import uuid4
from datetime import datetime
from nostr_sdk import Keys
from database import mongodb  # Ensure your MongoDB connection is set up

class UserService:
    collection_name = "users"

    def generate_nostr_key_pair(self, prefix: str):
        """
        Generate a Nostr key pair repeatedly until the public key starts with the given prefix.
        Returns:
            tuple: (private_key, public_key)
        """
        while True:
            keys = Keys.generate()
            private_key = keys.secret_key()
            public_key = keys.public_key()
            print(f"Generated Public Key: {public_key.to_bech32()}")
            print(f"Generated Private Key: {private_key.to_bech32()}")
            if public_key.to_bech32().startswith(prefix):
                print(f"Public key starts with '{prefix}'")
                return private_key, public_key

    async def register_user(self,lightning_address: str) -> dict:
        """
        Register a new user by generating a Nostr key pair.
        Only the public key is stored in the database.
        Returns:
            A dict containing user id, public key, private key, and creation timestamp.
        """
        prefix = "npub1mrkt"
        # Generate Nostr key pair; we need both for the returned response.
        private_key, public_key = self.generate_nostr_key_pair(prefix)

        user_id = uuid4()
        created_at = datetime.utcnow()

        # Build the user record for MongoDB (without the private key)
        user_record = {
            "id": str(user_id),
            "nostr_public_key": public_key.to_bech32(),
            "created_at": created_at,
            "lighting_address": lightning_address,
        }
        # MongoDB document _id is set to the user's id (as a string)
        user_record["_id"] = str(user_id)

        # Insert the user record into MongoDB
        collection = mongodb.db[self.collection_name]
        result = await collection.insert_one(user_record)
        print(f"Inserted user with id: {result.inserted_id}")

        # Build the response which includes both keys.
        response = {
            "id": str(user_id),
            "nostr_public_key": public_key.to_bech32(),
            "nostr_private_key": private_key.to_bech32(),  # Return the private key to the user
            "created_at": created_at,
            "lightning_address": lightning_address,
        }
        return response

# Instantiate a singleton of the service for use in routers.
user_service = UserService()
