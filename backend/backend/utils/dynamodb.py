import boto3
from stravalib.protocol import AccessInfo
from pydantic import BaseModel
from botocore.exceptions import ClientError
from typing import Any
from fastapi import HTTPException
import datetime as dt

# DynamoDB client setup
dynamodb = boto3.resource("dynamodb")
USER_TABLE_NAME = "user-table"
user_table = dynamodb.Table(USER_TABLE_NAME)

DOWNLOAD_STATUS_NAME = "download-status-table"
download_status_table = dynamodb.Table(DOWNLOAD_STATUS_NAME)


class UserTable(BaseModel):
    session_token: str
    athlete_id: int
    access_token: str
    refresh_token: str
    expires_at: int


class DownloadStatusTable(BaseModel):
    athlete_id: int
    last_download_time: int
    status: str


def save_user_data_to_dynamo(
    session_token: str, athlete_id: int, access_info: AccessInfo
) -> Any:
    try:
        # Use the attributes from the Pydantic model
        response = user_table.update_item(
            Key={"session_token": session_token},
            UpdateExpression=(
                "SET access_token = :access_token, "
                "refresh_token = :refresh_token, "
                "expires_at = :expires_at, "
                "athlete_id = :athlete_id"
            ),
            ExpressionAttributeValues={
                ":access_token": access_info["access_token"],
                ":refresh_token": access_info["refresh_token"],
                ":expires_at": access_info["expires_at"],
                ":athlete_id": athlete_id,
            },
            ReturnValues="ALL_NEW",
        )
        print(f"Successfully upserted user {athlete_id}.")
        return response
    except ClientError as e:
        print(f"Error upserting user: {e.response['Error']['Message']}")
        return None


def get_athlete_id_from_session_token(session_token: str) -> int:
    try:
        response = user_table.get_item(Key={"session_token": session_token})
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {str(e)}")

    response = user_table.get_item(Key={"session_token": session_token})
    if "Item" not in response:
        raise Exception(f"Can't find athlete with session token: {session_token}")
    return int(response["Item"]["athlete_id"])


def get_user_data_row_for_athlete(session_token: str) -> UserTable:
    try:
        response = user_table.get_item(Key={"session_token": session_token})
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {str(e)}")

    response = user_table.get_item(Key={"session_token": session_token})
    if "Item" not in response:
        raise Exception(f"Can't find athlete with session token: {session_token}")
    return UserTable(
        session_token=response["Item"]["session_token"],
        athlete_id=response["Item"]["athlete_id"],
        access_token=response["Item"]["access_token"],
        refresh_token=response["Item"]["refresh_token"],
        expires_at=response["Item"]["expires_at"],
    )


def save_download_status_to_dynamo(athlete_id: int, download_time: dt.datetime) -> Any:
    try:
        # Use the attributes from the Pydantic model
        response = download_status_table.update_item(
            Key={"athlete_id": athlete_id},
            UpdateExpression=("SET last_download_time = :last_download_time"),
            ExpressionAttributeValues={
                ":last_download_time": int(download_time.timestamp()),
            },
            ReturnValues="ALL_NEW",
        )
        print(f"Successfully upserted athlete: {athlete_id}.")
        return response
    except ClientError as e:
        print(f"Error upserting athlete: {e.response['Error']['Message']}")
        return None


def get_download_status_from_dynamo(athlete_id: int) -> str | None:
    """
    Returns a string of the latest download status for a user from dynamodb,
    and just returns None if there isn't a status.
    """

    try:
        response = download_status_table.get_item(Key={"athlete_id": athlete_id})
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {str(e)}")

    if "Item" not in response:
        return None
    else:
        row = DownloadStatusTable(
            athlete_id=response["Item"]["athlete_id"],
            last_download_time=response["Item"]["last_download_time"],
            status=response["Item"]["status"],
        )
        return row.status


def get_last_downloaded_time_from_dynamo(athlete_id: int) -> dt.datetime | None:
    """
    Returns the time that data was last downloaded for the given athlete, and
    None if it's never been downloaded.
    """
    try:
        response = download_status_table.get_item(Key={"athlete_id": athlete_id})
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {str(e)}")

    if "Item" not in response:
        return None
    else:
        row = DownloadStatusTable(
            athlete_id=response["Item"]["athlete_id"],
            last_download_time=response["Item"]["last_download_time"],
            status=response["Item"]["status"],
        )
        return dt.datetime.fromtimestamp(row.last_download_time)
