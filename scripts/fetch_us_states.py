import csv, time, requests
from datetime import datetime, timezone, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES   = ["https://www.googleapis.com/auth/searchtrends"]
BASE_URL = "https://searchtrends.googleapis.com/v1alpha"

creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
headers = {"Authorization": f"Bearer {creds.token}"}

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

end_time = datetime.now(timezone.utc) - timedelta(days=3)
start_time = end_time - timedelta(days=1795)


def poll(op_name):
    for _ in range(30):
        r = requests.get(f"{BASE_URL}/operations/{op_name}", headers=headers)
        r.raise_for_status()
        d = r.json()
        if d.get("done"):
            return d
        time.sleep(2)
    raise TimeoutError


all_rows = []
for code, name in STATES.items():
    print(f"Fetching {name} (US-{code})...")
    body = {"spec": {
        "expression": {"terms": [{"value": "food bank", "type": "BROAD"}]},
        "geo": {"type": "GEO_TYPE_ADMINISTRATIVE_AREA1", "code": f"US-{code}"},
        "timeRange": {
            "startTime": {"seconds": int(start_time.timestamp())},
            "endTime":   {"seconds": int(end_time.timestamp())},
        },
        "timeResolution": "MONTH",
    }}
    r = requests.post(f"{BASE_URL}:fetchTimeSeries", headers=headers, json=body)
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text[:200]}")
        continue
    data = poll(r.json()["name"])
    pts = data["response"]["timeSeries"]["points"]
    nonzero = sum(1 for p in pts if p["searchInterest"] > 0)
    print(f"  {len(pts)} months, {nonzero} non-zero")
    for pt in pts:
        all_rows.append({
            "state_code": code,
            "state_name": name,
            "period_start": pt["timeRange"]["startTime"],
            "period_end": pt["timeRange"]["endTime"],
            "search_interest": pt["searchInterest"],
            "scaled_search_interest": pt["scaledSearchInterest"],
            "is_partial": pt.get("isPartial", False),
        })
    time.sleep(0.5)

out = "data/food_bank_trends_us_states_monthly.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
    w.writeheader()
    w.writerows(all_rows)
print(f"\nDone. {len(all_rows)} rows written to {out}")
