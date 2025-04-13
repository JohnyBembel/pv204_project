import urllib
from typing import List, Dict, Any, Optional, cast
from datetime import datetime
from uuid import UUID, uuid4

from nostr_sdk import Tag, TagKind

from models.listing import ListingCreate, ListingInDB, ListingUpdate
from models.invoice import Invoice
from database import mongodb
from pydantic.validators import Decimal
from services.nostr_service import nostr_service

from services.nwc import processNWCstring, makeInvoice, getInfo, checkInvoice, tryToPayInvoice, didPaymentSucceed




class InvoiceService:
    """Service for handling LN invoices"""

    collection_name = "invoices"
    async def get_nwc_info(self,nwc_string: str) -> Any:
        return processNWCstring(nwc_string)

    async def create_invoice(self,nwc_seller_string, amount: int, description="") -> Invoice:
        nwc_info = processNWCstring(nwc_seller_string)
        nwc_info['relay'] = urllib.parse.unquote(nwc_info['relay'])
        amnt = amount
        if description:
            desc = description
        try:
            invoice_info = makeInvoice(nwc_info, amnt, desc)
        except Exception as e:
            print(f"Error creating an invoice: {e}")
        invoice = Invoice(**invoice_info["result"])

        return invoice

    async def check_invoice_status(self,nwc_string,invoicestr) -> Invoice:
        nwc_info = processNWCstring(nwc_string)
        nwc_info['relay'] = urllib.parse.unquote(nwc_info['relay'])
        result = checkInvoice(nwc_info, invoicestr)
        return result

    async def try_to_pay_invoice(self,nwc_buyer_string, invoicestr) -> Invoice:
        nwc_info = processNWCstring(nwc_buyer_string)
        nwc_info['relay'] = urllib.parse.unquote(nwc_info['relay'])
        result = tryToPayInvoice(nwc_info, invoicestr)
        return result

    async def check_payment(self, nwc_buyer_string, invoicestr) -> bool:
        result = await self.check_invoice_status(nwc_buyer_string, invoicestr)
        return (
                result and
                "result" in result and
                result["result"].get("settled_at") is not None
        )


invoice_service = InvoiceService()