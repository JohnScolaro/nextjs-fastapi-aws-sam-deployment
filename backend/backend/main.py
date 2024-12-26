from fastapi import FastAPI, HTTPException
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import boto3
from pydantic import BaseModel
from botocore.exceptions import ClientError
import logging
import sys

load_dotenv()

# DynamoDB client setup
dynamodb = boto3.resource("dynamodb")
table_name = "test-table"  # Replace with your DynamoDB table name
table = dynamodb.Table(table_name)

# Check if the app is running in development mode
is_dev = os.getenv("ENV", "production") == "development"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if is_dev else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

app = FastAPI(debug=True)
handler = Mangum(app)


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


# Define a Pydantic model for user data
class User(BaseModel):
    user_id: str
    name: str
    email: str


# Helper function to get a user from DynamoDB
def get_user_from_dynamodb(user_id: str):
    try:
        response = table.get_item(Key={"user_id": user_id})
        return response.get("Item")
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching user: {e.response['Error']['Message']}",
        )


# Helper function to save a user to DynamoDB
def save_user_to_dynamodb(user: User):
    try:
        table.put_item(
            Item={"user_id": user.user_id, "name": user.name, "email": user.email}
        )
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving user: {e.response['Error']['Message']}",
        )


# Helper function to delete a user from DynamoDB
def delete_user_from_dynamodb(user_id: str):
    try:
        table.delete_item(Key={"user_id": user_id})
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting user: {e.response['Error']['Message']}",
        )


# API endpoint to get user data
@app.get("/users/{user_id}")
def get_user(user_id: str):
    user = get_user_from_dynamodb(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# API endpoint to set user data
@app.post("/users/")
def create_user(user: User):
    save_user_to_dynamodb(user)
    return {"message": "User created successfully"}


# API endpoint to delete a user
@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    user = get_user_from_dynamodb(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    delete_user_from_dynamodb(user_id)
    return {"message": f"User {user_id} deleted successfully"}
