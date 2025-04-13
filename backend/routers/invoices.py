from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
from uuid import UUID, uuid4

from auth.dependencies import get_current_user
from models.listing import ListingCreate, ListingResponse, ListingUpdate, ListingSearchParams
from pydantic import BaseModel
from services.listing_service import listing_service
from models.invoice import Invoice

from services.invoice_service import invoice_service

from services.invoice_service import InvoiceService


router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
    responses={404: {"description": "invoice not found"}},
)
@router.get("/nwc_info/", response_model=Any)
async def get_nwc_info(nwc_string: str):
    """Get NWC info based on a provided NWC string."""
    try:
        # Call the InvoiceService to get NWC information
        nwc_info = await invoice_service.get_nwc_info(nwc_string)
        print(type(nwc_info))
        return nwc_info
    except Exception as e:
        # Handle any errors that may occur
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_invoice/", response_model=Invoice)
async def create_invoice(nwc_seller_string:str,amount:int,description:str):
    """Create a new Lightning Network invoice."""
    try:
        # Create an instance of the InvoiceService and call create_invoice
        invoice_service = InvoiceService()
        invoice = await invoice_service.create_invoice(nwc_seller_string,amount,description)
        return invoice  # FastAPI will serialize the Invoice object to JSON automatically
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating invoice: {e}")

@router.get("/check_invoice_status/")
async def check_invoice_status(nwc_string:str,invoicestr: str):
    """Get Lightning Network invoice status."""
    result = await invoice_service.check_invoice_status(nwc_string,invoicestr)
    return result

@router.post("/try_to_pay_invoice/")
async def try_to_pay_invoice(nwc_buyer_string:str,invoicestr: str):
    """Try to pay an LN invoice."""
    result = await invoice_service.try_to_pay_invoice(nwc_buyer_string,invoicestr)
    return result

@router.get("/check_payment/")
async def check_payment(nwc_buyer_string:str,invoicestr: str):
    """Verify LN payment status."""
    result = await invoice_service.check_payment(nwc_buyer_string,invoicestr)
    return result