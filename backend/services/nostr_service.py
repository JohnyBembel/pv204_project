import hashlib
import os
import secrets
import time
from typing import Dict, List
from dotenv import load_dotenv
from nostr_sdk import Keys, Client, EventBuilder, NostrSigner, Tag

load_dotenv()


class NostrService:
    """
    A generic Nostr service for publishing various types of events
    to the Nostr network using the nostr-sdk library
    """

    def __init__(self, private_key_hex: str = None, relays: List[str] = None):
        """
        Initialize the Nostr service

        Args:
            private_key_hex: Hex string of private key
            relays: List of relay URLs
        """
        self.private_key_hex = private_key_hex
        self.relays = relays if relays else ["ws://localhost:8080"]
        self.client = None
        self.signer = None
        self.is_connected = False

    def _generate_unique_id(self):
        """Generate a unique ID for events."""
        timestamp = str(time.time())
        random_bytes = secrets.token_bytes(16)
        combined = timestamp.encode() + random_bytes
        unique_id = hashlib.sha256(combined).hexdigest()[:32]

        return unique_id

    async def connect(self):
        """Connect to Nostr relays"""
        if self.is_connected:
            return

        try:
            # Parse keys from hex
            keys = Keys.parse(self.private_key_hex)
            print(f'Using Nostr key: {keys.public_key().to_bech32()}')

            # Create signer and client
            self.signer = NostrSigner.keys(keys)
            self.client = Client(self.signer)

            # Add relays
            for relay in self.relays:
                await self.client.add_relay(relay)

            # Connect to relays
            await self.client.connect()
            self.is_connected = True
            print(f"Connected to {len(self.relays)} Nostr relay(s)")
        except Exception as e:
            print(f"Error connecting to Nostr relays: {e}")
            self.is_connected = False

    async def ensure_connected(self):
        """Ensure we're connected to relays before operations"""
        if not self.is_connected:
            await self.connect()

    async def publish_event(self,
                            content: str,
                            tags: List[Tag] = None) -> Dict[str, str]:
        """
        Publish a generic event to Nostr relays with an automatically generated unique identifier.

        Args:
            content: Content of the event
            tags: List of Tag objects to include (optional)
            kind: Kind of the event (default: 1 for text_note)

        Returns:
            Dictionary with event_id and identifier
        """
        await self.ensure_connected()

        if not self.client or not self.signer:
            print("Nostr client not initialized properly")
            return {
                "event_id": "nostr-error-not-initialized",
                "identifier": ""
            }

        try:
            # Generate a unique identifier
            unique_id = self._generate_unique_id()

            # Create a list of tags if none provided
            if tags is None:
                tags = []

            # Always add our identifier tag
            identifier_tag = Tag.identifier(unique_id)
            tags.append(identifier_tag)

            # Create the event builder
            builder = EventBuilder.text_note(content)

            # Add tags
            for tag in tags:
                builder = builder.tags([tag])

            # Sign and send the event
            event = await builder.sign(self.signer)
            result = await self.client.send_event(event)

            # Get the event ID - store only the hex format
            event_id = event.id().to_hex()
            event_id_bech32 = event.id().to_bech32()

            print(f"Published event to Nostr: {event_id_bech32} with identifier: {unique_id}")

            return {
                "event_id": event_id,
                "identifier": unique_id
            }
        except Exception as e:
            print(f"Error publishing to Nostr: {e}")
            return {
                "event_id": f"nostr-error-{str(e)}",
                "identifier": ""
            }

    async def publish_update(self,
                             content: str,
                             previous_event_id: str,
                             tags: List[Tag] = None) -> Dict[str, str]:
        """
        Publish an update to a previous Nostr event, referencing the original event.
        """
        await self.ensure_connected()

        if not self.client or not self.signer:
            print("Nostr client not initialized properly")
            return {
                "event_id": "nostr-error-not-initialized",
                "identifier": ""
            }

        try:
            # Generate a unique identifier
            unique_id = self._generate_unique_id()

            # Initialize tags list if none provided
            if tags is None:
                tags = []

            # Add identifier tag
            identifier_tag = Tag.identifier(unique_id)
            tags.append(identifier_tag)

            tags.append(Tag.parse(["e", previous_event_id]))

            # Create the event builder
            builder = EventBuilder.text_note(content)

            # Add all tags - one at a time to avoid issues
            for tag in tags:
                builder = builder.tags([tag])

            # Sign and send the event
            event = await builder.sign(self.signer)
            result = await self.client.send_event(event)

            # Get the event ID in hex format
            event_id = event.id().to_hex()
            event_id_bech32 = event.id().to_bech32()

            print(f"Published update to Nostr: {event_id_bech32} with identifier: {unique_id}")

            return {
                "event_id": event_id,
                "identifier": unique_id
            }
        except Exception as e:
            print(f"Error publishing update to Nostr: {e}")
            return {
                "event_id": f"nostr-error-{str(e)}",
                "identifier": ""
            }

    async def close(self):
        """Close connections to relays"""
        if self.client and self.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            print("Disconnected from Nostr relays")

# load env variables
private_key_hex = os.getenv("NOSTR_PRIVATE_KEY")
relays = os.getenv("NOSTR_RELAYS", "ws://localhost:8080").split(",")

if not private_key_hex:
    raise ValueError("NOSTR_PRIVATE_KEY environment variable is not set")
if not relays:
    raise ValueError("NOSTR_RELAYS environment variable is not set")

# Create a singleton instance
nostr_service = NostrService(
    private_key_hex=private_key_hex,
    relays=relays,
)