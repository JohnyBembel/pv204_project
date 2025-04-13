from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
from uuid import UUID, uuid4

from auth.dependencies import get_current_user
from models.listing import ListingCreate, ListingResponse, ListingUpdate
from pydantic import BaseModel
from services.listing_service import listing_service
from models.invoice import Invoice

from services.invoice_service import invoice_service

from services.invoice_service import InvoiceService


class CreateInvoiceRequest(BaseModel):
    amount: int
    description: str = ""



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

@router.post("/", response_model=Invoice)
async def create_invoice(request: CreateInvoiceRequest):
    """Create a new Lightning Network invoice."""
    try:
        # Create an instance of the InvoiceService and call create_invoice
        invoice_service = InvoiceService()
        invoice = await invoice_service.create_invoice(request.amount, request.description)
        return invoice  # FastAPI will serialize the Invoice object to JSON automatically
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating invoice: {e}")