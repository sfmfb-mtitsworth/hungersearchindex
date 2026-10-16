import json, requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timezone, timedelta

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/searchtrends'])
if creds.expired: creds.refresh(Request())
headers = {'Authorization': 'Bearer ' + creds.token}

BASE = 'https://searchtrends.googleapis.com/v1alpha'
end_time = datetime.now(timezone.utc) - timedelta(days=3)
start_time = end_time.replace(year=end_time.year - 3)

for geo_type, code in [
    ('GEO_TYPE_ADMINISTRATIVE_AREA1', 'US-CA'),
    ('GEO_TYPE_ADMINISTRATIVE_AREA1', 'US-NY'),
]:
    body = {'spec': {
        'expression': {'terms': [{'value': 'food bank', 'type': 'BROAD'}]},
        'geo': {'type': geo_type, 'code': code},
        'timeRange': {
            'startTime': {'seconds': int(start_time.timestamp())},
            'endTime': {'seconds': int(end_time.timestamp())},
        },
        'timeResolution': 'MONTH',
    }}
    r = requests.post(f'{BASE}:fetchTimeSeries', headers=headers, json=body)
    print(code, r.status_code, r.text[:300])
