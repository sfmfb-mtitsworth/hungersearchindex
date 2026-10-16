from google_auth_oauthlib.flow import InstalledAppFlow

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

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
creds = flow.run_local_server(port=8888, open_browser=True)
with open("token.json", "w") as f:
    f.write(creds.to_json())
print("Re-authorized. token.json updated.")
