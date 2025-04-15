import json
import asyncio
import websockets
from bech32 import bech32_decode, convertbits
from typing import List, Optional, Dict, Any
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NostrWebSocketFinder:
    """
    A class to find Nostr profiles using direct WebSocket connections to relays
    """

    def __init__(self, relays: List[str] = None):
        """
        Initialize with a list of relay URLs

        Args:
            relays: List of WebSocket relay URLs (wss:// or ws://)
        """
        # Default relays if none provided
        if relays is None:
            # Get relays from environment or use defaults
            env_relays = os.getenv("NOSTR_RELAYS", "ws://localhost:8080").split(",")
            # Add some well-known public relays for better discovery
            public_relays = [
                "wss://relay.damus.io/",
                "wss://nos.lol/",
                "wss://relay.nostr.info/",
                "wss://relay.nostr.band/"
            ]
            # Combine and remove duplicates
            self.relays = list(set(env_relays + public_relays))
        else:
            self.relays = relays

    def npub_to_hex(self, npub: str) -> str:
        """
        Convert an npub key to hex format

        Args:
            npub: The public key in npub format

        Returns:
            The public key in hex format
        """
        if npub.startswith("npub1"):
            hrp, data = bech32_decode(npub)
            if hrp != "npub":
                raise ValueError("Invalid npub")
            data_bytes = convertbits(data, 5, 8, False)
            return bytes(data_bytes).hex()
        return npub  # Assume it's already hex if not starting with npub1

    async def get_profile_from_relay(self, pubkey: str, relay: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get profile information from a specific relay

        Args:
            pubkey: The public key in hex format
            relay: The relay URL
            timeout: Timeout in seconds

        Returns:
            Profile data or None if not found
        """
        try:
            # Convert pubkey to hex if it's in npub format
            pubkey_hex = self.npub_to_hex(pubkey)

            logger.info(f"Connecting to relay: {relay}")
            async with websockets.connect(relay, ping_interval=None, close_timeout=timeout) as ws:
                # Create a subscription for kind 0 events from this author
                subscription_id = "find-profile-" + pubkey_hex[:8]
                req = ["REQ", subscription_id, {"kinds": [0], "authors": [pubkey_hex]}]
                await ws.send(json.dumps(req))
                logger.info(f"Sent request to {relay}: {req}")

                # Set a timeout for the entire operation
                try:
                    profile_data = None
                    event_id = None
                    created_at = None
                    kind = None

                    # Wait for responses with timeout
                    while True:
                        try:
                            # Wait for a response with timeout
                            response_text = await asyncio.wait_for(ws.recv(), timeout=timeout)
                            response = json.loads(response_text)

                            # Check if it's an EVENT message and kind 0
                            if response[0] == "EVENT" and response[2]["kind"] == 0:
                                try:
                                    metadata = json.loads(response[2]["content"])
                                    event_id = response[2]["id"]
                                    pubkey = response[2]["pubkey"]
                                    created_at = response[2]["created_at"]
                                    kind = response[2]["kind"]

                                    logger.info(f"Found profile on {relay}: {metadata}")

                                    # Add additional metadata
                                    metadata["_event_id"] = event_id
                                    metadata["_pubkey"] = pubkey
                                    metadata["_created_at"] = created_at
                                    metadata["_kind"] = kind

                                    profile_data = metadata
                                    break
                                except json.JSONDecodeError:
                                    logger.warning(f"Invalid JSON in profile content: {response[2]['content']}")

                            # Check if we've reached the end of stored events
                            if response[0] == "EOSE":
                                logger.info(f"End of stored events from {relay}")
                                break
                        except asyncio.TimeoutError:
                            logger.warning(f"Timeout waiting for response from {relay}")
                            break

                    # Close the subscription
                    close_msg = ["CLOSE", subscription_id]
                    await ws.send(json.dumps(close_msg))

                    return profile_data

                except asyncio.TimeoutError:
                    logger.warning(f"Overall timeout for {relay}")
                    return None

        except Exception as e:
            logger.error(f"Error connecting to {relay}: {str(e)}")
            return None

    async def find_profile(self, pubkey: str, timeout: int = 5, timeout_secs: int = None) -> Optional[Dict[str, Any]]:
        """
        Search for a profile across multiple relays

        Args:
            pubkey: The public key (npub or hex format)
            timeout: Timeout in seconds for each relay
            timeout_secs: Alternative parameter name for backward compatibility

        Returns:
            Profile data or None if not found on any relay
        """
        # Use timeout_secs if provided, otherwise use timeout
        effective_timeout = timeout_secs if timeout_secs is not None else timeout

        # Create tasks for all relays
        relay_tasks = []
        for relay in self.relays:
            task = asyncio.create_task(self.get_profile_from_relay(pubkey, relay, effective_timeout))
            relay_tasks.append(task)

        try:
            # Use asyncio.wait with return_when=FIRST_COMPLETED to get the first completed task
            done, pending = await asyncio.wait(
                relay_tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Check if we have a successful result from any completed task
            for task in done:
                try:
                    result = task.result()
                    if result:
                        # Found a profile, cancel all pending tasks
                        for pending_task in pending:
                            pending_task.cancel()
                        return result
                except Exception as e:
                    logger.error(f"Task error: {str(e)}")

            # If no result found yet, wait for remaining tasks with a timeout
            if pending:
                try:
                    more_done, still_pending = await asyncio.wait(
                        pending,
                        timeout=effective_timeout
                    )

                    # Check results from newly completed tasks
                    for task in more_done:
                        try:
                            result = task.result()
                            if result:
                                # Cancel any remaining tasks
                                for p in still_pending:
                                    p.cancel()
                                return result
                        except Exception as e:
                            logger.error(f"Task error: {str(e)}")

                    # Cancel any remaining tasks
                    for p in still_pending:
                        p.cancel()

                except asyncio.TimeoutError:
                    # Cancel all tasks on timeout
                    for p in pending:
                        p.cancel()

        except Exception as e:
            logger.error(f"Error in find_profile: {str(e)}")
            # Make sure all tasks are cancelled on error
            for task in relay_tasks:
                if not task.done():
                    task.cancel()

        # If we get here, no profile was found on any relay
        return None


# Create a singleton instance with default relays
websocket_finder = NostrWebSocketFinder()