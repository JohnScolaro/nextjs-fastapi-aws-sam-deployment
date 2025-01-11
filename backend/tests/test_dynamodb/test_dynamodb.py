from moto import mock_aws
import boto3
from backend.utils.dynamodb import (
    get_athlete_id_from_session_token,
    get_last_downloaded_time_from_dynamo,
    save_download_status_to_dynamo,
    get_download_status_from_dynamo,
    get_user_data_row_for_athlete,
    USER_TABLE_NAME,
    DOWNLOAD_STATUS_NAME,
)
import pytest
import datetime as dt


@mock_aws
def test_get_athlete_id_from_session_token_when_athlete_doesnt_exist():
    name = USER_TABLE_NAME
    conn = boto3.client(
        "dynamodb",
        region_name="ap-southeast-2",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )
    conn.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "session_token", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "session_token", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    with pytest.raises(Exception, match="Can't find athlete"):
        get_athlete_id_from_session_token("no_athlete_session_token")


@mock_aws
def test_get_athlete_id_from_session_token_when_athlete_does_exist():
    name = USER_TABLE_NAME
    conn = boto3.client(
        "dynamodb",
        region_name="ap-southeast-2",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )
    conn.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "session_token", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "session_token", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    conn.put_item(
        TableName=USER_TABLE_NAME,
        Item={
            "session_token": {"S": "example_session_token"},
            "athlete_id": {"N": "1"},
            "access_token": {"S": "a"},
            "refresh_token": {"S": "b"},
            "expires_at": {"N": "2"},
        },
    )
    assert get_athlete_id_from_session_token("example_session_token") == 1


@mock_aws
def test_save_data_status_to_dynamodb() -> None:
    name = DOWNLOAD_STATUS_NAME
    conn = boto3.client(
        "dynamodb",
        region_name="ap-southeast-2",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )
    conn.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "athlete_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "athlete_id", "AttributeType": "N"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    save_download_status_to_dynamo(1, dt.datetime(2020, 1, 2))
    request = conn.get_item(
        TableName=DOWNLOAD_STATUS_NAME, Key={"athlete_id": {"N": "1"}}
    )
    assert "Item" in request
    assert int(request["Item"]["athlete_id"]["N"]) == 1


@mock_aws
def test_get_last_downloaded_time_from_dynamo_when_it_doesnt_exist() -> None:
    name = DOWNLOAD_STATUS_NAME
    conn = boto3.client(
        "dynamodb",
        region_name="ap-southeast-2",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )
    conn.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "athlete_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "athlete_id", "AttributeType": "N"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    assert get_last_downloaded_time_from_dynamo(1) is None


@mock_aws
def test_get_last_downloaded_time_from_dynamo() -> None:
    name = DOWNLOAD_STATUS_NAME
    conn = boto3.client(
        "dynamodb",
        region_name="ap-southeast-2",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )
    conn.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "athlete_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "athlete_id", "AttributeType": "N"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    conn.put_item(
        TableName=DOWNLOAD_STATUS_NAME,
        Item={
            "athlete_id": {"N": "1"},
            "last_download_time": {"N": str(int(dt.datetime(2021, 3, 4).timestamp()))},
            "status": {"S": "yeet"},
        },
    )
    assert get_last_downloaded_time_from_dynamo(1) == dt.datetime(2021, 3, 4)


@mock_aws
def test_get_last_downloaded_status_from_dynamo_when_it_doesnt_exist() -> None:
    name = DOWNLOAD_STATUS_NAME
    conn = boto3.client(
        "dynamodb",
        region_name="ap-southeast-2",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )
    conn.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "athlete_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "athlete_id", "AttributeType": "N"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    assert get_download_status_from_dynamo(1) is None


@mock_aws
def test_get_last_downloaded_status_from_dynamo() -> None:
    name = DOWNLOAD_STATUS_NAME
    conn = boto3.client(
        "dynamodb",
        region_name="ap-southeast-2",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )
    conn.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "athlete_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "athlete_id", "AttributeType": "N"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    conn.put_item(
        TableName=DOWNLOAD_STATUS_NAME,
        Item={
            "athlete_id": {"N": "1"},
            "last_download_time": {"N": str(int(dt.datetime(2021, 3, 4).timestamp()))},
            "status": {"S": "yeet"},
        },
    )
    assert get_download_status_from_dynamo(1) == "yeet"


@mock_aws
def test_get_user_data_row_for_athlete():
    name = USER_TABLE_NAME
    conn = boto3.client(
        "dynamodb",
        region_name="ap-southeast-2",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )
    conn.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "session_token", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "session_token", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    conn.put_item(
        TableName=USER_TABLE_NAME,
        Item={
            "session_token": {"S": "example_session_token"},
            "athlete_id": {"N": "1"},
            "access_token": {"S": "a"},
            "refresh_token": {"S": "b"},
            "expires_at": {"N": "2"},
        },
    )

    row = get_user_data_row_for_athlete("example_session_token")
    assert row.session_token == "example_session_token"
    assert row.athlete_id == 1
    assert row.access_token == "a"
    assert row.refresh_token == "b"
    assert row.expires_at == 2
