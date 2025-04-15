from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any
from models.review import ReviewCreate, ReviewResponse
from services.review_service import review_service
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)

@router.post("/", response_model=ReviewResponse)
async def create_review(review: ReviewCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        buyer_pubkey = current_user["nostr_public_key"]
        result = await review_service.create_review(review, buyer_pubkey)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating review: {str(e)}")
    
@router.delete("/{review_id}", status_code=204)
async def delete_review(review_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        result = await review_service.delete_review(review_id, current_user["pubkey"])
        if not result:
            raise HTTPException(status_code=404, detail="review not found or not authorized to delete")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error deleting review: {str(e)}")

@router.get("/seller/{seller_pubkey}", response_model=List[ReviewResponse])
async def get_seller_reviews(seller_pubkey: str):
    try:
        reviews = await review_service.get_reviews_for_seller(seller_pubkey)
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving reviews: {str(e)}")

@router.get("/trust-score/{seller_pubkey}", response_model=float)
async def get_seller_trust_score(seller_pubkey: str):
    try:
        score = await review_service.calculate_trust_score(seller_pubkey)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error calculating trust score: {str(e)}")