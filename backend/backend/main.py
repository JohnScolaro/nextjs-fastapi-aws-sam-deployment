from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

app = FastAPI()
handler = Mangum(app)

load_dotenv()

# Define allowed origins (your frontend's domain)
origins = [
    "http://localhost:3000",  # Default URL of next.js's dev frontend for development
    os.environ["DOMAIN"],  # Prod domain from environment variables.
]

# Add CORSMiddleware to your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specifies allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def read_root():
    return {"message": "This is a test message, returned by lambda with mangum"}


@app.get("/api/example")
async def example():
    return {"message": "This is an example API call :)"}


@app.get("/something/else")
async def read_something_else():
    return {"message": "something else :)"}


@app.get("/items/{item_name}")
async def read_item_name(item_name):
    return {"message": f"You requested: {item_name}"}
