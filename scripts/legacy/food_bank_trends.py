import csv
import json
import time
import requests
import os
from datetime import datetime, timezone, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

env = dict(line.split("=", 1) for line in open(".env").read().splitlines() if "=" in line)

CLIENT_CONFIG = {
    "installed": {
        "client_id": env["client_id"],
        "client_secret": env["client_secret"],
        "redirect_uris": ["http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}
SCOPES = ["https://www.googleapis.com/auth/searchtrends"]
TOKEN_FILE = "token.json"
BASE_URL = "https://searchtrends.googleapis.com/v1alpha"

creds = None
if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
        creds = flow.run_local_server(port=8888, open_browser=False)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

headers = {"Authorization": f"Bearer {creds.token}"}

# All California DMAs
CA_DMAS = {
    "800": "Bakersfield",
    "803": "Los Angeles",
    "807": "San Francisco-Oakland-San Jose",
    "813": "Chico-Redding",
    "825": "San Diego",
    "828": "Monterey-Salinas",
    "855": "Eureka",
    "862": "Sacramento-Stockton-Modesto",
    "866": "Fresno-Visalia",
    "868": "Santa Barbara-Santa Maria-San Luis Obispo",
}

start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
end_time = datetime.now(timezone.utc) - timedelta(days=3)

EXPRESSION = {"terms": [{"value": "food bank", "type": "BROAD"}]}


def poll_operation(operation_name):
    for attempt in range(20):
        r = requests.get(f"{BASE_URL}/operations/{operation_name}", headers=headers)
        r.raise_for_status()
        result = r.json()
        if result.get("done"):
            return result
        print(f"    Not ready, retrying in 2s... (attempt {attempt + 1})")
        time.sleep(2)
    raise TimeoutError("Operation timed out.")


all_rows = []

for dma_code, dma_name in CA_DMAS.items():
    print(f"Fetching {dma_name} (DMA {dma_code})...")

    body = {
        "spec": {
            "expression": EXPRESSION,
            "geo": {"type": "GEO_TYPE_DESIGNATED_MARKET_AREA", "code": dma_code},
            "timeRange": {
                "startTime": {"seconds": int(start_time.timestamp())},
                "endTime": {"seconds": int(end_time.timestamp())},
            },
            "timeResolution": "WEEK",
        }
    }

    r = requests.post(f"{BASE_URL}:fetchTimeSeries", headers=headers, json=body)
    r.raise_for_status()
    result = poll_operation(r.json()["name"])

    points = result["response"]["timeSeries"]["points"]
    for pt in points:
        all_rows.append({
            "dma_code": dma_code,
            "dma_name": dma_name,
            "week_start": pt["timeRange"]["startTime"],
            "week_end": pt["timeRange"]["endTime"],
            "search_interest": pt["searchInterest"],
            "scaled_search_interest": pt["scaledSearchInterest"],
            "is_partial": pt.get("isPartial", False),
        })
    print(f"  -> {len(points)} weeks retrieved")
    time.sleep(0.5)  # be polite to the API

output_file = "food_bank_trends_california_dma.csv"
fieldnames = ["dma_code", "dma_name", "week_start", "week_end",
              "search_interest", "scaled_search_interest", "is_partial"]

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"\nDone. {len(all_rows)} rows written to {output_file}")
