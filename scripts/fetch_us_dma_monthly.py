"""Fetch monthly "food bank" search interest for every US DMA (Nielsen media market),
following the same pattern as fetch_monthly_all.py (which covers only the 10 CA DMAs).

DMA_CODES below is the authoritative list of 210 codes returned live by the Trends API's
own fetchGeoBreakdown endpoint (country US, breakdownResolution=GEO_TYPE_DESIGNATED_MARKET_AREA) —
not copied from a third-party source, so it's guaranteed to match what fetchTimeSeries accepts.

DMA_NAMES is best-effort only. Google's API returns codes but no display names, so names come
from a third-party CSV (github.com/fissehab/Nielsen-Media-Research-DMA). That source is already
known to be WRONG for at least two of our own already-verified CA codes (813, 855, 868 vs its
813=Medford-Klamath Falls, 855=Santa Barbara, 868=Chico-Redding — likely stale from before Nielsen
renumbered those markets), so treat any name with verified=False as a label to spot-check, not fact.
The `name_verified` column in the output CSV flags which names are known-correct vs. third-party guesses.
"""
import csv, time, requests, os
from datetime import datetime, timezone, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

env = dict(line.split("=", 1) for line in open(".env").read().splitlines() if "=" in line)
SCOPES   = ["https://www.googleapis.com/auth/searchtrends"]
BASE_URL = "https://searchtrends.googleapis.com/v1alpha"

creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
headers = {"Authorization": f"Bearer {creds.token}"}

# code -> (name, name_verified)
DMA_NAMES = {
    "500": ("Portland-Auburn", False),
    "501": ("New York", False),
    "502": ("Binghamton", False),
    "503": ("Macon", False),
    "504": ("Philadelphia", False),
    "505": ("Detroit", False),
    "506": ("Boston (Manchester)", False),
    "507": ("Savannah", False),
    "508": ("Pittsburgh", False),
    "509": ("Ft. Wayne", False),
    "510": ("Cleveland-Akron (Canton)", False),
    "511": ("Washington, DC (Hagrstwn)", False),
    "512": ("Baltimore", False),
    "513": ("Flint-Saginaw-Bay City", False),
    "514": ("Buffalo", False),
    "515": ("Cincinnati", False),
    "516": ("Erie", False),
    "517": ("Charlotte", False),
    "518": ("Greensboro-H.Point-W.Salem", False),
    "519": ("Charleston, SC", False),
    "520": ("Augusta-Aiken", False),
    "521": ("Providence-New Bedford", False),
    "522": ("Columbus, GA (Opelika, AL)", False),
    "523": ("Burlington-Plattsburgh", False),
    "524": ("Atlanta", False),
    "525": ("Albany, GA", False),
    "526": ("Utica", False),
    "527": ("Indianapolis", False),
    "528": ("Miami-Ft. Lauderdale", False),
    "529": ("Louisville", False),
    "530": ("Tallahassee-Thomasville", False),
    "531": ("Tri-Cities, TN-VA", False),
    "532": ("Albany-Schenectady-Troy", False),
    "533": ("Hartford & New Haven", False),
    "534": ("Orlando-Daytona Bch-Melbrn", False),
    "535": ("Columbus, OH", False),
    "536": ("Youngstown", False),
    "537": ("Bangor", False),
    "538": ("Rochester, NY", False),
    "539": ("Tampa-St. Pete (Sarasota)", False),
    "540": ("Traverse City-Cadillac", False),
    "541": ("Lexington", False),
    "542": ("Dayton", False),
    "543": ("Springfield-Holyoke", False),
    "544": ("Norfolk-Portsmth-Newpt Nws", False),
    "545": ("Greenville-N.Bern-Washngtn", False),
    "546": ("Columbia, SC", False),
    "547": ("Toledo", False),
    "548": ("West Palm Beach-Ft. Pierce", False),
    "549": ("Watertown", False),
    "550": ("Wilmington", False),
    "551": ("Lansing", False),
    "552": ("Presque Isle", False),
    "553": ("Marquette", False),
    "554": ("Wheeling-Steubenville", False),
    "555": ("Syracuse", False),
    "556": ("Richmond-Petersburg", False),
    "557": ("Knoxville", False),
    "558": ("Lima", False),
    "559": ("Bluefield-Beckley-Oak Hill", False),
    "560": ("Raleigh-Durham (Fayetvlle)", False),
    "561": ("Jacksonville", False),
    "563": ("Grand Rapids-Kalmzoo-B.Crk", False),
    "564": ("Charleston-Huntington", False),
    "565": ("Elmira (Corning)", False),
    "566": ("Harrisburg-Lncstr-Leb-York", False),
    "567": ("Greenvll-Spart-Ashevll-And", False),
    "569": ("Harrisonburg", False),
    "570": ("Myrtle Beach-Florence", False),
    "571": ("Ft. Myers-Naples", False),
    "573": ("Roanoke-Lynchburg", False),
    "574": ("Johnstown-Altoona-St Colge", False),
    "575": ("Chattanooga", False),
    "576": ("Salisbury", False),
    "577": ("Wilkes Barre-Scranton-Hztn", False),
    "581": ("Terre Haute", False),
    "582": ("Lafayette, IN", False),
    "583": ("Alpena", False),
    "584": ("Charlottesville", False),
    "588": ("South Bend-Elkhart", False),
    "592": ("Gainesville", False),
    "596": ("Zanesville", False),
    "597": ("Parkersburg", False),
    "598": ("Clarksburg-Weston", False),
    "600": ("Corpus Christi", False),
    "602": ("Chicago", False),
    "603": ("Joplin-Pittsburg", False),
    "604": ("Columbia-Jefferson City", False),
    "605": ("Topeka", False),
    "606": ("Dothan", False),
    "609": ("St. Louis", False),
    "610": ("Rockford", False),
    "611": ("Rochestr-Mason City-Austin", False),
    "612": ("Shreveport", False),
    "613": ("Minneapolis-St. Paul", False),
    "616": ("Kansas City", False),
    "617": ("Milwaukee", False),
    "618": ("Houston", False),
    "619": ("Springfield, MO", False),
    "622": ("New Orleans", False),
    "623": ("Dallas-Ft. Worth", False),
    "624": ("Sioux City", False),
    "625": ("Waco-Temple-Bryan", False),
    "626": ("Victoria", False),
    "627": ("Wichita Falls & Lawton", False),
    "628": ("Monroe-El Dorado", False),
    "630": ("Birmingham (Ann and Tusc)", False),
    "631": ("Ottumwa-Kirksville", False),
    "632": ("Paducah-Cape Girard-Harsbg", False),
    "633": ("Odessa-Midland", False),
    "634": ("Amarillo", False),
    "635": ("Austin", False),
    "636": ("Harlingen-Wslco-Brnsvl-McA", False),
    "637": ("Cedar Rapids-Wtrlo-IWC&Dub", False),
    "638": ("St. Joseph", False),
    "639": ("Jackson, TN", False),
    "640": ("Memphis", False),
    "641": ("San Antonio", False),
    "642": ("Lafayette, LA", False),
    "643": ("Lake Charles", False),
    "644": ("Alexandria, LA", False),
    "647": ("Greenwood-Greenville", False),
    "648": ("Champaign&Sprngfld-Decatur", False),
    "649": ("Evansville", False),
    "650": ("Oklahoma City", False),
    "651": ("Lubbock", False),
    "652": ("Omaha", False),
    "656": ("Panama City", False),
    "657": ("Sherman-Ada", False),
    "658": ("Green Bay-Appleton", False),
    "659": ("Nashville", False),
    "661": ("San Angelo", False),
    "662": ("Abilene-Sweetwater", False),
    "669": ("Madison", False),
    "670": ("Ft. Smith-Fay-Sprngdl-Rgrs", False),
    "671": ("Tulsa", False),
    "673": ("Columbus-Tupelo-W Pnt-Hstn", False),
    "675": ("Peoria-Bloomington", False),
    "676": ("Duluth-Superior", False),
    "678": ("Wichita-Hutchinson Plus", False),
    "679": ("Des Moines-Ames", False),
    "682": ("Davenport-R.Island-Moline", False),
    "686": ("Mobile-Pensacola (Ft Walt)", False),
    "687": ("Minot-Bsmrck-Dcknsn(Wlstn)", False),
    "691": ("Huntsville-Decatur (Flor)", False),
    "692": ("Beaumont-Port Arthur", False),
    "693": ("Little Rock-Pine Bluff", False),
    "698": ("Montgomery-Selma", False),
    "702": ("La Crosse-Eau Claire", False),
    "705": ("Wausau-Rhinelander", False),
    "709": ("Tyler-Longview(Lfkn&Ncgd)", False),
    "710": ("Hattiesburg-Laurel", False),
    "711": ("Meridian", False),
    "716": ("Baton Rouge", False),
    "717": ("Quincy-Hannibal-Keokuk", False),
    "718": ("Jackson, MS", False),
    "722": ("Lincoln & Hastings-Krny", False),
    "724": ("Fargo-Valley City", False),
    "725": ("Sioux Falls(Mitchell)", False),
    "734": ("Jonesboro", False),
    "736": ("Bowling Green", False),
    "737": ("Mankato", False),
    "740": ("North Platte", False),
    "743": ("Anchorage", False),
    "744": ("Honolulu", False),
    "745": ("Fairbanks", False),
    "746": ("Biloxi-Gulfport", False),
    "747": ("Juneau", False),
    "749": ("Laredo", False),
    "751": ("Denver", False),
    "752": ("Colorado Springs-Pueblo", False),
    "753": ("Phoenix (Prescott)", False),
    "754": ("Butte-Bozeman", False),
    "755": ("Great Falls", False),
    "756": ("Billings", False),
    "757": ("Boise", False),
    "758": ("Idaho Fals-Pocatllo(Jcksn)", False),
    "759": ("Cheyenne-Scottsbluff", False),
    "760": ("Twin Falls", False),
    "762": ("Missoula", False),
    "764": ("Rapid City", False),
    "765": ("El Paso (Las Cruces)", False),
    "766": ("Helena", False),
    "767": ("Casper-Riverton", False),
    "770": ("Salt Lake City", False),
    "771": ("Yuma-El Centro", False),
    "773": ("Grand Junction-Montrose", False),
    "789": ("Tucson (Sierra Vista)", False),
    "790": ("Albuquerque-Santa Fe", False),
    "798": ("Glendive", False),
    "800": ("Bakersfield", True),
    "801": ("Eugene", False),
    "802": ("Eureka?? (unreliable — 855 is our verified Eureka code)", False),
    "803": ("Los Angeles", True),
    "804": ("Palm Springs", False),
    "807": ("San Francisco-Oakland-San Jose", True),
    "810": ("Yakima-Pasco-Rchlnd-Knnwck", False),
    "811": ("Reno", False),
    "813": ("Chico-Redding", True),
    "819": ("Seattle-Tacoma", False),
    "820": ("Portland, OR", False),
    "821": ("Bend, OR", False),
    "825": ("San Diego", True),
    "828": ("Monterey-Salinas", True),
    "839": ("Las Vegas", False),
    "855": ("Eureka", True),
    "862": ("Sacramento-Stockton-Modesto", True),
    "866": ("Fresno-Visalia", True),
    "868": ("Santa Barbara-Santa Maria-San Luis Obispo", True),
    "881": ("Spokane", False),
}

# The 210 codes below were pulled live from the Trends API itself via fetchGeoBreakdown
# (country US, breakdownResolution=GEO_TYPE_DESIGNATED_MARKET_AREA) on 2026-09-10 — these
# are guaranteed valid, unlike DMA_NAMES which is a third-party best guess.
DMA_CODES = sorted(DMA_NAMES.keys(), key=int)

start_time = datetime.now(timezone.utc) - timedelta(days=3 + 365 * 3)
end_time   = datetime.now(timezone.utc) - timedelta(days=3)

OUT = "data/archive/food_bank_trends_us_dma_monthly.csv"
FIELDNAMES = [
    "dma_code", "dma_name", "name_verified",
    "period_start", "period_end",
    "search_interest", "scaled_search_interest", "is_partial",
]


def poll(op_name):
    for _ in range(30):
        r = requests.get(f"{BASE_URL}/operations/{op_name}", headers=headers)
        r.raise_for_status()
        d = r.json()
        if d.get("done"):
            return d
        time.sleep(2)
    raise TimeoutError(f"operation {op_name} did not finish in time")


def refresh_if_needed():
    global headers
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        headers = {"Authorization": f"Bearer {creds.token}"}


# Resumable: skip DMAs already present in an existing output file (from a prior run that hit
# the daily quota partway through), so re-running doesn't re-spend quota on DMAs we already have.
already_have = {}  # dma_code -> list of row dicts
if os.path.exists(OUT):
    with open(OUT, newline="", encoding="utf-8") as rf:
        for row in csv.DictReader(rf):
            already_have.setdefault(row["dma_code"], []).append(row)
    if already_have:
        print(f"Found {len(already_have)} DMA(s) already fetched in {OUT}; skipping those.")

codes_to_fetch = [c for c in DMA_CODES if c not in already_have]

total_rows = sum(len(v) for v in already_have.values())
failed = []
quota_exhausted = False
for i, code in enumerate(codes_to_fetch, 1):
    name, verified = DMA_NAMES[code]
    print(f"[{i}/{len(codes_to_fetch)}] Fetching {name} (DMA {code})...")
    refresh_if_needed()
    body = {"spec": {
        "expression": {"terms": [{"value": "food bank", "type": "BROAD"}]},
        "geo": {"type": "GEO_TYPE_DESIGNATED_MARKET_AREA", "code": code},
        "timeRange": {
            "startTime": {"seconds": int(start_time.timestamp())},
            "endTime":   {"seconds": int(end_time.timestamp())},
        },
        "timeResolution": "MONTH",
    }}
    r = requests.post(f"{BASE_URL}:fetchTimeSeries", headers=headers, json=body)
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text[:200]}")
        failed.append(code)
        if r.status_code == 429:
            print("Daily API quota exhausted — stopping early instead of burning through the "
                  "rest of the list on requests that will all fail. Re-run this script after "
                  "the quota resets (~24h) to pick up where it left off.")
            quota_exhausted = True
            break
        continue
    try:
        data = poll(r.json()["name"])
    except TimeoutError as e:
        print(f"  {e}")
        failed.append(code)
        continue
    pts = data["response"]["timeSeries"]["points"]
    nonzero = sum(1 for p in pts if p["searchInterest"] > 0)
    print(f"  {len(pts)} months, {nonzero} non-zero")
    new_rows = []
    for pt in pts:
        new_rows.append({
            "dma_code": code,
            "dma_name": name,
            "name_verified": verified,
            "period_start": pt["timeRange"]["startTime"],
            "period_end":   pt["timeRange"]["endTime"],
            "search_interest": pt["searchInterest"],
            "scaled_search_interest": pt["scaledSearchInterest"],
            "is_partial": pt.get("isPartial", False),
        })
    already_have[code] = new_rows
    total_rows += len(new_rows)

    # Rewrite the full file after every DMA (existing + newly fetched so far) so progress is
    # never lost, whether this run finishes cleanly or hits the quota wall.
    with open(OUT, "w", newline="", encoding="utf-8") as wf:
        w = csv.DictWriter(wf, fieldnames=FIELDNAMES)
        w.writeheader()
        for c in DMA_CODES:
            for row in already_have.get(c, []):
                w.writerow(row)
    time.sleep(0.5)

print(f"\nDone (for now). {total_rows} rows across {len(already_have)}/{len(DMA_CODES)} DMAs in {OUT}")
still_missing = [c for c in DMA_CODES if c not in already_have]
if still_missing:
    print(f"{len(still_missing)} DMA(s) still missing: {still_missing}")
    if quota_exhausted:
        print("Re-run this script once the daily quota resets to fetch the rest.")
