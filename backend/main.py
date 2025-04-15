import json
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import Message

from routers import invoices
from database import mongodb
from routers import listings, users, auth, reviews
from services.nostr_service import nostr_service
from services.user_service import user_service


# Create a lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to the database and Nostr
    mongodb.connect_to_mongo()
    print("Connected to MongoDB")

    # Initialize Nostr connection
    try:
        print("Initializing Nostr connection...")
        await nostr_service.connect()
        if nostr_service.is_connected:
            print("✅ Successfully connected to Nostr network")
        else:
            print("⚠️ Nostr connection not established")
    except Exception as e:
        print(f"❌ Error connecting to Nostr relays: {e}")
        print("Continuing without Nostr integration")

    yield  # This is where FastAPI runs and serves requests

    # Shutdown: Close connections
    print("Shutting down...")
    try:
        await nostr_service.close()
        print("Nostr connections closed")
    except Exception as e:
        print(f"Error closing Nostr connection: {e}")

    mongodb.close_mongo_connection()
    print("All connections closed")

# Pass the lifespan to FastAPI
app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_request_body(request: Request, call_next):
    # Only log for POST requests (or check request.url.path for specific endpoints)
    if request.method == "POST":
        # Read the body. Note that reading it consumes it.
        body_bytes = await request.body()
        # Print the raw body. If the body is JSON, you can also pretty-print it.
        try:
            body = body_bytes.decode("utf-8")
            parsed_body = json.loads(body)
            print("DEBUG: Incoming request body:", json.dumps(parsed_body, indent=2))
        except Exception:
            print("DEBUG: Incoming request body (raw):", body_bytes)

        # Create a new receive function so downstream handlers can read the body again.
        async def receive() -> Message:
            return {"type": "http.request", "body": body_bytes}

        # Replace the request's stream with our custom receive function.
        request._receive = receive

    response = await call_next(request)
    return response
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(reviews.router)

app.include_router(invoices.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}