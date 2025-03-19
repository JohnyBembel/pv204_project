from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4

from models.listing import ListingCreate, ListingInDB, ListingUpdate
from database import mongodb
from services.nostr_service import nostr_service


class ListingService:
    """Service for handling listing operations with MongoDB and Nostr"""

    collection_name = "listings"

    @staticmethod
    def _serialize_listing(listing_dict: Dict[Any, Any]) -> Dict[Any, Any]:
        """Convert UUID, datetime, and Pydantic objects to strings for MongoDB"""
        result = {}
        for key, value in listing_dict.items():
            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value
            elif isinstance(value, dict):
                result[key] = ListingService._serialize_listing(value)
            elif isinstance(value, list):
                result[key] = [
                    ListingService._serialize_listing(item) if isinstance(item, dict) else
                    str(item) if hasattr(item, '__str__') and not isinstance(item, (str, int, float, bool)) else item
                    for item in value
                ]
            elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool)):
                # Convert Pydantic types (like HttpUrl) to strings
                result[key] = str(value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _deserialize_listing(db_listing: Dict[Any, Any]) -> Dict[Any, Any]:
        """Convert MongoDB document to a format compatible with Pydantic models"""
        if db_listing is None:
            return None

        # Handle ObjectId
        if "_id" in db_listing:
            db_listing["id"] = str(db_listing["_id"])
            del db_listing["_id"]

        return db_listing

    async def create_listing(self, listing_data: ListingCreate, seller_id: UUID) -> ListingInDB:
        """
        Create a new listing in MongoDB and publish to Nostr

        Args:
            listing_data: Listing data from request
            seller_id: ID of the seller

        Returns:
            Created listing with database ID
        """
        # Convert to dict for easier manipulation
        listing_dict = listing_data.dict()

        # Add database fields
        listing_dict["id"] = uuid4()
        listing_dict["seller_id"] = seller_id
        listing_dict["created_at"] = datetime.utcnow()
        listing_dict["updated_at"] = datetime.utcnow()
        listing_dict["status"] = "active"
        listing_dict["views_count"] = 0
        listing_dict["favorite_count"] = 0

        # Convert image URLs to Image objects with string URLs
        listing_dict["images"] = [
            {"url": str(url), "is_primary": idx == 0}
            for idx, url in enumerate(listing_dict["images"])
        ]

        # Prepare for MongoDB insertion
        mongo_listing = self._serialize_listing(listing_dict)

        # Store the object ID for the listing (convert UUID to string)
        mongo_listing["_id"] = str(listing_dict["id"])

        # Publish to Nostr
        try:
            # Get the result of the coroutine, not the coroutine itself
            nostr_event_id = await nostr_service.publish_listing(listing_dict)
            mongo_listing["nostr_event_id"] = nostr_event_id
            listing_dict["nostr_event_id"] = nostr_event_id
        except Exception as e:
            print(f"Error publishing to Nostr: {e}")
            # Continue anyway, we can sync later

        # Insert into MongoDB
        collection = mongodb.db[self.collection_name]
        await collection.insert_one(mongo_listing)

        # Return the created listing
        return ListingInDB(**listing_dict)

    async def get_listing(self, listing_id: str) -> Optional[Dict[Any, Any]]:
        """
        Get a listing by ID from MongoDB

        Args:
            listing_id: ID of the listing

        Returns:
            Listing data or None if not found
        """
        collection = mongodb.db[self.collection_name]
        listing = await collection.find_one({"_id": listing_id})

        if not listing:
            return None

        return self._deserialize_listing(listing)

    async def update_listing(self, listing_id: str, listing_update: ListingUpdate) -> Optional[Dict[Any, Any]]:
        """
        Update a listing in MongoDB and Nostr

        Args:
            listing_id: ID of the listing to update
            listing_update: New listing data

        Returns:
            Updated listing or None if not found
        """
        collection = mongodb.db[self.collection_name]

        # Get the existing listing
        existing = await collection.find_one({"_id": listing_id})
        if not existing:
            return None

        # Convert to a mutable dict and deserialize
        existing = self._deserialize_listing(existing)

        # Apply updates
        update_data = listing_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            existing[key] = value

        # Update timestamp
        existing["updated_at"] = datetime.utcnow()

        # Prepare for MongoDB update
        mongo_listing = self._serialize_listing(existing)

        # Update in MongoDB
        result = await collection.replace_one({"_id": listing_id}, mongo_listing)

        if result.modified_count == 0:
            return None

        # Update in Nostr if we have a Nostr event ID
        if "nostr_event_id" in existing and existing["nostr_event_id"]:
            try:
                new_event_id = await nostr_service.update_listing(
                    existing["nostr_event_id"],
                    existing
                )
                # Update the Nostr event ID in MongoDB
                await collection.update_one(
                    {"_id": listing_id},
                    {"$set": {"nostr_event_id": new_event_id}}
                )
                existing["nostr_event_id"] = new_event_id
            except Exception as e:
                print(f"Error updating in Nostr: {e}")
                # Continue anyway

        return existing

    async def delete_listing(self, listing_id: str) -> bool:
        """
        Delete a listing from MongoDB only (not from Nostr)

        Args:
            listing_id: ID of the listing to delete

        Returns:
            True if successful, False otherwise
        """
        collection = mongodb.db[self.collection_name]

        # Get the listing first to check if it exists
        listing = await collection.find_one({"_id": listing_id})

        if not listing:
            return False

        # Delete from MongoDB
        result = await collection.delete_one({"_id": listing_id})

        return result.deleted_count > 0

    async def search_listings(self, params: Dict[str, Any]) -> List[Dict[Any, Any]]:
        """
        Search for listings with filters

        Args:
            params: Search parameters

        Returns:
            List of matching listings
        """
        collection = mongodb.db[self.collection_name]

        # Build the query
        query = {}

        # Status filter
        if "status" in params and params["status"]:
            query["status"] = params["status"]

        # Keyword search
        if "keyword" in params and params["keyword"]:
            keyword = params["keyword"]
            query["$or"] = [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}}
            ]

        # Category filter
        if "category_id" in params and params["category_id"]:
            query["category_id"] = params["category_id"]

        # Price range
        price_filter = {}
        if "min_price" in params and params["min_price"] is not None:
            price_filter["$gte"] = params["min_price"]
        if "max_price" in params and params["max_price"] is not None:
            price_filter["$lte"] = params["max_price"]
        if price_filter:
            query["price"] = price_filter

        # Condition filter
        if "condition" in params and params["condition"]:
            query["condition"] = params["condition"]

        # Seller filter
        if "seller_id" in params and params["seller_id"]:
            query["seller_id"] = str(params["seller_id"])

        # Auction filter
        if "is_auction" in params and params["is_auction"] is not None:
            query["is_auction"] = params["is_auction"]

        # Sort options
        sort_field = params.get("sort_by", "created_at")
        sort_order = 1 if params.get("sort_order", "desc") == "asc" else -1
        sort_options = [(sort_field, sort_order)]

        # Pagination
        skip = params.get("offset", 0)
        limit = params.get("limit", 20)

        # Execute query
        cursor = collection.find(query).sort(sort_options).skip(skip).limit(limit)

        # Process results
        results = []
        async for document in cursor:
            results.append(self._deserialize_listing(document))

        return results

    async def increment_view_count(self, listing_id: str) -> bool:
        """
        Increment the view count for a listing

        Args:
            listing_id: ID of the listing

        Returns:
            True if successful, False otherwise
        """
        collection = mongodb.db[self.collection_name]
        result = await collection.update_one(
            {"_id": listing_id},
            {"$inc": {"views_count": 1}}
        )
        return result.modified_count > 0

    async def sync_with_nostr(self, listing_id: str) -> bool:
        """
        Republish a listing to Nostr if it doesn't have a Nostr event ID

        Args:
            listing_id: ID of the listing

        Returns:
            True if successful, False otherwise
        """
        collection = mongodb.db[self.collection_name]
        listing = await collection.find_one({"_id": listing_id})

        if not listing:
            return False

        if "nostr_event_id" in listing and listing["nostr_event_id"]:
            # Already has a Nostr event ID
            return True

        # Deserialize for Nostr
        listing_dict = self._deserialize_listing(listing)

        # Publish to Nostr
        try:
            nostr_event_id = await nostr_service.publish_listing(listing_dict)
            # Update the Nostr event ID in MongoDB
            await collection.update_one(
                {"_id": listing_id},
                {"$set": {"nostr_event_id": nostr_event_id}}
            )
            return True
        except Exception as e:
            print(f"Error publishing to Nostr: {e}")
            return False


# Create a service instance
listing_service = ListingService()