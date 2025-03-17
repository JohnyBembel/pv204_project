from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import mongodb


# Create a lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to the database
    mongodb.connect_to_mongo()

    yield  # This is where FastAPI runs and serves requests

    # Shutdown: Close the database connection
    mongodb.close_mongo_connection()


# Pass the lifespan to FastAPI
app = FastAPI(lifespan=lifespan)

# Create a data model
class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    active: bool = True

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


# Create user endpoint
@app.post("/users/", response_model=User)
async def create_user(user: User):
    try:
        # Convert Pydantic model to dict
        user_dict = user.dict()

        # Insert the user into MongoDB
        result = await mongodb.db.users.insert_one(user_dict)

        # Check if the insertion was successful
        if result.inserted_id:
            # Return the created user
            return user
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Get all users endpoint
@app.get("/users/")
async def get_users():
    try:
        users = []
        cursor = mongodb.db.users.find({})
        async for document in cursor:
            # Convert MongoDB ObjectId to string for JSON serialization
            if "_id" in document:
                document["id"] = str(document["_id"])
                del document["_id"]
            users.append(document)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
