from typing import Dict, Any, List, Optional
from models.review import ReviewCreate, ReviewResponse
from services.pop_service import proof_of_purchase_service
from database import mongodb

class ReviewService:
    async def create_review(self, review_data: ReviewCreate, seller_pubkey: str) -> ReviewResponse:

        if review_data.rating < 1 or review_data.rating > 5:
            raise ValueError("Rating must be an integer between 1 and 5")
        
        review = {
            "transaction_id": review_data.transaction_id,
            "seller_pubkey": seller_pubkey,
            "rating": review_data.rating,
            "comment": review_data.comment,
            "verified": True
        }
        
        collection = mongodb.db["reviews"]
        result = await collection.find_one({"transaction_id": review_data.transaction_id})
        if result:
            raise ValueError("Review already exists for this transaction")
        
        await collection.insert_one(review)

        
        return ReviewResponse(**review)
    
    async def get_reviews_for_seller(self, seller_pubkey: str) -> List[ReviewResponse]:
        collection = mongodb.db["reviews"]
        cursor = collection.find({"seller_pubkey": seller_pubkey, "verified": True})

        reviews = await cursor.to_list(length=8)
        return [ReviewResponse(**review) for review in reviews]
    
    async def calculate_trust_score(self, seller_pubkey: str) -> float:
        """
        Calculate trust score for a seller based on verified reviews
        Trust score = sum of ratings / number of reviews
        """
        reviews = await self.get_reviews_for_seller(seller_pubkey)
        
        if not reviews:
            return 0.0
            
        total_stars = sum(review.rating for review in reviews)
        return total_stars / len(reviews)

review_service = ReviewService()