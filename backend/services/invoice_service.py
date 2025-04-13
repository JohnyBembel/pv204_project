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

from services.nwc import processNWCstring, makeInvoice, getInfo


class InvoiceService:
    """Service for handling LN invoices"""

    collection_name = "invoices"
    async def get_nwc_info(self,nwc_string: str) -> Any:
        return processNWCstring(nwc_string)

    async def create_invoice(self, amount: Decimal, description="") -> Invoice:
        #TODO: query DB for NWC instead of fixed NWC
        nwc_info = processNWCstring("nostr+walletconnect://1291af9c119879ef7a59636432c6e06a7a058c0cae80db27c0f20f61f3734e52?relay=wss%3A%2F%2Fnwc.primal.net%2Fcbrg6yqrsa9hcnsliv8a6q8wxtexd7&secret=bc09b5caf6895a43905dc01afa64ede5d4edbed693a1bc671e77aaeea3244a99")
        print(nwc_info)
        nwc_info['relay'] = urllib.parse.unquote(nwc_info['relay'])
        amnt = amount
        if description:
            desc = description
        try:
            invoice_info = makeInvoice(nwc_info, amnt, desc)
        except Exception as e:
            print(f"Error creating an invoice: {e}")
        invoice = Invoice(
            amnt=Decimal(amnt),
            desc=desc,
            nwcstring="nostr+walletconnect://1291af9c119879ef7a59636432c6e06a7a058c0cae80db27c0f20f61f3734e52?relay=wss%3A%2F%2Fnwc.primal.net%2Fcbrg6yqrsa9hcnsliv8a6q8wxtexd7&secret=bc09b5caf6895a43905dc01afa64ede5d4edbed693a1bc671e77aaeea3244a99"
        )
        print(invoice_info)
        return invoice

#    async def check_invoice_status(self,invoice):

invoice_service = InvoiceService()