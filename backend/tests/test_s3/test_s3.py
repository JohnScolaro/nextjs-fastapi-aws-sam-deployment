from moto import mock_aws
from backend.utils.s3 import (
    save_summary_activities_to_s3,
    get_summary_activities_from_s3,
)
import boto3
from backend.utils.s3 import BUCKET_NAME


@mock_aws
def test_saving_activity_roundtrip(some_basic_runs_and_rides) -> None:
    region = "ap-southeast-2"
    s3_client = boto3.client("s3", region_name=region)
    s3_client.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={"LocationConstraint": region},
    )

    save_summary_activities_to_s3(123, some_basic_runs_and_rides)
    reloaded_activities = get_summary_activities_from_s3(123)

    for fixture_activity, reloaded_activity in zip(
        some_basic_runs_and_rides, reloaded_activities
    ):
        assert fixture_activity == reloaded_activity
