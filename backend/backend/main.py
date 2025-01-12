from fastapi import FastAPI, WebSocket
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import json
from typing import Any
from stravalib.model import SummaryActivity
from stravalib.util.limiter import RateLimiter
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from stravalib.client import Client
from stravalib.exc import RateLimitExceeded
from stravalib.model import DetailedAthlete
from backend.utils.environment_variables import evm
from backend.utils.s3 import (
    is_there_any_data_for_athlete,
    get_age_of_data_for_athlete,
    delete_athlete_data,
    save_summary_activities_to_s3,
)
from typing import Type
import secrets
from backend.utils.dynamodb import (
    save_user_data_to_dynamo,
    get_athlete_id_from_session_token,
    get_last_downloaded_time_from_dynamo,
    save_download_status_to_dynamo,
    get_download_status_from_dynamo,
    get_user_data_row_for_athlete,
)
import httpx
from requests.exceptions import HTTPError
from backend.communication_schema import DataStatusMessage
import dataclasses
from backend.gui.gui import get_all_tabs, tab_tree
from backend.tabs.tab_group import TabGroup
from backend.tabs.tabs import Tab
from backend.utils.routes import unauthorized_if_no_session_token
import datetime as dt

# Check if the app is running in development mode
is_dev = os.getenv("ENVIRONMENT", "production") == "development"

# # Configure logging
# logging.basicConfig(
#     level=logging.DEBUG if is_dev else logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     stream=sys.stdout,
# )

logger = logging.getLogger(__name__)

app = FastAPI(debug=True)
handler = Mangum(app)


def get_frontend_base_url() -> str:
    return f"{evm.get_protocol()}://{evm.get_domain()}:{evm.get_frontend_port()}"


def get_backend_base_url() -> str:
    return f"{evm.get_protocol()}://{evm.get_domain()}:{evm.get_backend_port()}"


# Define allowed origins (your frontend's domain)
origins = [
    get_frontend_base_url(),  # Default URL of next.js's dev frontend for development
]

# Add CORSMiddleware to your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specifies allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/api/example_chart_data")
def chart_data(request: Request) -> Any:
    current_file_dir_path = os.path.dirname(os.path.realpath(__file__))
    example_chart_data_path = os.path.join(
        current_file_dir_path, "static", "example_charts", "personal_bests.json"
    )
    # Read the example file
    with open(example_chart_data_path, "r") as f:
        json_data = f.read()

    chart_json = json.loads(json_data)
    return chart_json


@app.get("/api/authenticate")
def authenticate(request: Request) -> Any:
    # Retrieve query parameters
    code: str = request.query_params["code"]
    scope: str = request.query_params["scope"]

    # Do some terrible scope checking.
    # If we aren't given permission to read activities, just return to index.
    if scope != "read,activity:read":
        return RedirectResponse("/?scope_incorrect=true")

    # Try the following. It can fail in a couple different ways, all due to
    # hitting the Strava rate limit.
    try:
        client = Client()
        token_response = client.exchange_code_for_token(
            client_id=evm.get_strava_client_id(),
            client_secret=evm.get_strava_client_secret(),
            code=code,
        )
        # Get the access token and immediately use that to get the athlete id.
        client.access_token = token_response["access_token"]
        athlete: DetailedAthlete = client.get_athlete()

        # Create a unique session token.
        session_token = secrets.token_urlsafe(32)

        # Save all these important secrets to dynamodb
        save_user_data_to_dynamo(session_token, athlete.id, token_response)

        # Redirect to home while setting cookies.
        redirect_url = f"{get_frontend_base_url()}/home" if is_dev else "/home"
        response = RedirectResponse(url=redirect_url)
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=30 * 60,  # 30 mins
            httponly=True,
            secure=True,  # Ensure HTTPS is used in production.
            samesite="Strict"
            if evm.is_production()
            else "None",  # Prevent CSRF (but allow for local development.)
        )
    except (HTTPError, RateLimitExceeded) as e:
        return RedirectResponse("/?rate_limit_exceeded=true")

    response.set_cookie(
        key="logged_in",
        value="true",
        max_age=30 * 60,  # 30 mins.
        secure=True,  # Ensure HTTPS is used in production.
        samesite="Strict"
        if evm.is_production()
        else "None",  # Prevent CSRF (but allow for local development.)
    )
    return response


@app.get("/api/data_status", dependencies=[Depends(unauthorized_if_no_session_token)])
async def get_data_status(request: Request) -> Any:
    session_token = request.cookies.get("session_token")
    athlete_id = get_athlete_id_from_session_token(session_token)

    # Check if there is data at all.
    if is_there_any_data_for_athlete(athlete_id):
        # Check how old the data is.
        data_age = get_age_of_data_for_athlete(athlete_id)

        # If it's over a week old, delete and re-download.
        if data_age > dt.timedelta(days=7):
            # Delete the data
            delete_athlete_data(athlete_id)

            # Trigger re-download
            print("Help me 2")
            # Return message to say to continue polling.
            return DataStatusMessage(message="Downloading data", stop_polling=False)

        # If it's more recent that a week, well, the data is downloaded, so just return
        # that we already have the data. :)
        else:
            return DataStatusMessage(message="Data Downloaded", stop_polling=True)
    else:
        # We have no data, lets see if another lambda is currently downloading data,
        # because this can take a few seconds.
        status = get_download_status_from_dynamo(athlete_id)

        if status is None:
            # We don't have any download scheduled, so just trigger a new download.
            # await trigger_user_data_download(request.cookies)
            print("Help me 1")

            # Return message to say to continue polling.
            return DataStatusMessage(message="Downloading data", stop_polling=False)

        else:
            return DataStatusMessage(message=status, stop_polling=False)


async def trigger_user_data_download(cookies):
    """
    Call this function to trigger the data download, and return instantly.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Replace with the full URL when deployed (e.g., API Gateway URL)
            response = await client.post(
                f"{get_backend_base_url()}/api/download_data", cookies=cookies
            )
            print(f"Triggered data download task: {response.status_code}")
        except Exception as e:
            print(f"Failed to data download task: {e}")
    # Return instantly to the client
    return {"message": "Task triggered successfully"}


@app.get("/api/download_data", dependencies=[Depends(unauthorized_if_no_session_token)])
def download_data(request: Request) -> Any:
    """
    Downloading the dang data here please.
    """
    session_token = request.cookies.get("session_token")
    athlete_id = get_athlete_id_from_session_token(session_token)
    download_and_save_summary_statistics(
        athlete_id,
    )


def download_and_save_summary_statistics(athlete_id: int) -> None:
    logger.info(f"Getting Summary Statistics for {athlete_id}")

    client = get_client_for_athlete(athlete_id)

    summary_activities: list[SummaryActivity] = get_summary_activities(
        client, athlete_id
    )

    save_summary_activities_to_s3(athlete_id, summary_activities)


def get_client_for_athlete(
    session_token: str, rate_limiter: Type[RateLimiter] | None = None
) -> Client:
    """
    Given an athlete id, return a client with the key.
    """
    # Get required tokens.
    row = get_user_data_row_for_athlete(session_token)

    # Set the clients access token for the user.
    client = Client(access_token=row.access_token, rate_limiter=rate_limiter)
    return client


def get_summary_activities(client: Client, athlete_id: int) -> list[SummaryActivity]:
    """
    Gets all the summary activities and adds some logging around it.
    """
    logger.info(f"Getting summary activities for athlete: {athlete_id}")
    summary_activities: list[SummaryActivity] = list(client.get_activities())

    logger.info(
        f"Received {len(summary_activities)} activities for athlete: {athlete_id}"
    )
    return summary_activities


@dataclasses.dataclass
class SideMenuTabs:
    name: str
    key: str
    type: str
    items: list[Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "key": self.key,
            "type": self.type,
            "items": self.items,
        }


@app.get("/api/tabs", dependencies=[Depends(unauthorized_if_no_session_token)])
def get_tabs(request: Request) -> Any:
    def expand_tabs(tabs: list[Tab | TabGroup]) -> list[Any]:
        json_tabs = []
        for tab in tabs:
            if isinstance(tab, TabGroup):
                json_tabs.append(tab_to_dict(tab, items=expand_tabs(tab.children)))
            else:
                json_tabs.append(tab_to_dict(tab, items=[]))
        return json_tabs

    def tab_to_dict(tab: Tab | TabGroup, items: list[Any] = []) -> dict[str, Any]:
        return SideMenuTabs(
            name=tab.name, key=tab.get_key(), type=tab.get_type(), items=items
        ).to_dict()

    return expand_tabs(tab_tree)


# Before the app starts, we want to generate all the routes for our tabs.
for tab in get_all_tabs():
    tab.generate_and_register_route(app, evm)


# The data status connection is a websocket
@app.websocket(
    "/api/data_status", dependencies=[Depends(unauthorized_if_no_session_token)]
)
async def websocket_endpoint(websocket: WebSocket):
    session_token = websocket.cookies.get("session_token")
    athlete_id = get_athlete_id_from_session_token(session_token)
    await websocket.accept()
    print(athlete_id)
    while True:
        data = await websocket.receive_text()
        print(data)
        await websocket.send_text(f"Message text was: {data}")
