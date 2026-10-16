# California Hunger Signal

Search interest for **"food bank"** across California's 10 Designated Market Areas (DMAs), from the Google Trends API (alpha). The repo holds the data, the scripts that fetch it, and a static dashboard (`index.html`, no build step) that visualizes it.

A second line of work (not on the dashboard) compares national/state search series against Census Household Pulse Survey (HPS) food-insufficiency rates, to test whether the search signal tracks measured food insecurity.

## Data to share: California DMA monthly

[`data/food_bank_trends_california_dma_monthly_last24.csv`](data/food_bank_trends_california_dma_monthly_last24.csv) — Oct 2024 to Oct 2026, 10 DMAs, 250 rows. The full series (Jan 2024 onward) is [`data/food_bank_trends_california_dma_monthly.csv`](data/food_bank_trends_california_dma_monthly.csv).

| Column | Meaning |
|---|---|
| `dma_code`, `dma_name` | Nielsen DMA code and name |
| `period_start`, `period_end` | Month boundaries (UTC, end exclusive) |
| `search_interest` | Raw index value from the API (rounded). Comparable across DMAs |
| `scaled_search_interest` | 0–100, scaled within each DMA's own window. **Not** comparable across DMAs |
| `is_partial` | `True` for the current, incomplete month |

Caveats:
- The API is sampled: repeated pulls of the same month differ slightly, a few points on the 0–100 scale in large DMAs.
- Bakersfield (800), Chico-Redding (813) and Santa Barbara (868) have low query volume. Their values are noisy and have zero/missing months; don't read much into month-to-month changes.
- The most recent 3 days are excluded because the API's latest data is unreliable.

## Other data (`data/`)

- `food_bank_trends_california_dma.csv` — weekly series for the same 10 DMAs (read by the dashboard).
- `food_bank_trends_us_states_monthly.csv` — monthly series, 50 states + DC (~5-year window).
- `food_bank_trends_us_dma_monthly.csv` — monthly series, US DMAs.
- `hps_food_insufficiency_state.csv` — Census HPS food-insufficiency rate by state and period (`period, end_date, state_code, pct_insufficient, total_reporting`). Source: Census Household Pulse Survey public files; the raw workbooks are not stored in the repo.
- `term_validation_*.json`, `sparse_dmas_monthly.csv`, `food_bank_trends_arizona_monthly.csv` — one-off diagnostics for choosing the query term and checking low-volume geos.

## Refreshing the data

Run from the repo root. Requires Python 3 with `requests`, `google-auth` and `google-auth-oauthlib`.

```
python scripts/reauth.py              # refresh token.json (local OAuth, localhost:8888)
python scripts/fetch_monthly_all.py   # monthly CA DMAs -> data/food_bank_trends_california_dma_monthly.csv
python scripts/embed_data.py          # rebuild the data block inside index.html
```

`fetch_us_states.py` pulls the state series. Credentials live in `.env` (`client_id`, `client_secret`) and `token.json`; both are gitignored.

Scripts in `scripts/legacy/` are superseded and kept for reference only.
