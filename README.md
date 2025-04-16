# Nostr-based marketplace
This project uses FastAPI for the backend and React for the frontend.

## Requirements
<ul>
  <li>Python 3.8+</li>
  <li>Node.js 14+</li>
  <li>npm</li>
</ul>

## Setup

**Backend setup**

1. Navigate to the backend directory:

`cd backend`

3. Create a virtual environment:

`python -m venv venv`

3. Activate the virtual environment:

`venv\Scripts\activate`

4. Install dependencies:

`pip install -r requirements.txt`

5. Create a `.env` file in the backend directory.

**Important:** Email us about `.env` file and we will provide it for you.
We will listen on these email addresses: `567755@mail.muni.cz` or `ceska@mail.muni.cz`.

6. Start the FastAPI server with uvicorn:

`uvicorn app.main:app --reload --port 8000`

The API will be available at `http://localhost:8000`.

API documentation will be available at `http://localhost:8000/docs`.

**Frontend setup**

1. Navigate to the frontend directory:

`cd frontend`

2. Install dependencies:

`npm install`

3. Start the React development server:

`npm start`

The frontend will be available at `http://localhost:3000`

## Individual contributions

**Jakub Smorada** (also under username Ahearys)

1. MongoDB deployment
2. Authentication of user's private key
3. Sessions and their persistence on the frontend
4. Listings, Users, Nostr API and their frontend

**Ondřej  Češka**

1. Payment functionality, both on backend and frontend
2. Getting user's Nostr profile
3. Generating user's public and private key 

**Andrej Smatana**

1. Reviews
