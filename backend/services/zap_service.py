import urllib.parse
import httpx
from datetime import datetime
class ZapService:
    """Service for handling LN invoices via static Nostr Lightning Addresses"""

    async def get_lnurl_info(self, lightning_address: str) -> dict:
        """Resolve a Nostr Lightning Address to its LNURL-pay endpoint"""
        try:
            username, domain = lightning_address.split("@")
            url = f"https://{domain}/.well-known/lnurlp/{username}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            raise RuntimeError(f"Failed to resolve LNURL: {e}")

    async def create_invoice(self, lightning_address: str, amount_sats: int, comment: str = "") -> dict:
        """Request an invoice from a Nostr Lightning Address"""
        try:
            lnurl_info = await self.get_lnurl_info(lightning_address)
            callback_url = lnurl_info["callback"]
            params = {
                "amount": amount_sats * 1000,
            }
            if comment:
                params["comment"] = comment
            full_url = f"{callback_url}?{urllib.parse.urlencode(params)}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(full_url)
                resp.raise_for_status()
                response_data = resp.json()

                invoice_data = {
                    "type": "zap",
                    "invoice": response_data.get("pr", ""),
                    "payment_hash": response_data.get("payment_hash", ""),
                    "amount": amount_sats,
                    "fees_paid": 0,
                    "description": comment,
                    "created_at": datetime.now().timestamp(),
                }

                return invoice_data

        except Exception as e:
            raise RuntimeError(f"Failed to create zap invoice: {e}")


zap_service = ZapService()
