from fastapi import APIRouter, HTTPException
from services.zap_service import zap_service
from models.invoice import Invoice
from datetime import datetime

router = APIRouter(
    prefix="/zaps",
    tags=["zaps"],
    responses={404: {"description": "Zap not found"}},
)
@router.post("/create_zap_invoice/")
async def create_zap_invoice(nwc_seller_string: str, amount: int, description: str):
    try:

        zap_invoice = await zap_service.create_invoice(nwc_seller_string, amount, description)

        invoice_data = Invoice(
            type="zap",
            invoice=zap_invoice['invoice'],
            description=zap_invoice['description'],
            payment_hash=zap_invoice['payment_hash'],
            amount=zap_invoice['amount'],
            fees_paid=zap_invoice['fees_paid'],
            created_at=datetime.now().timestamp()
        )

        return invoice_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating zap invoice: {e}")
