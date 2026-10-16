# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Two related workstreams built on the Google Trends API (alpha, `searchtrends.googleapis.com/v1alpha`):

1. **The dashboard** — a static, single-file page ("California Hunger Signal") visualizing search interest for "food bank" across California's 10 Designated Market Areas (DMAs). Data is fetched to CSVs, then embedded directly into `index.html` as a JS object. No backend, no build step; `index.html` is opened/hosted as-is.
2. **Validation research** (newer, not yet on the page) — national/state-level search series plus Census Household Pulse Survey (HPS) food-insufficiency rates, used to check whether the search signal actually tracks measured food insecurity. Nothing in this workstream feeds `index.html`.

## Commands

No package manager, lockfile, or test suite. Scripts run directly with Python from the repo root — they use relative paths (`.env`, `token.json`, `data/...`), so **always run from the repo root**:

```
python scripts/reauth.py                 # refresh token.json via local OAuth flow on localhost:8888 (run first if a fetch 401s)
python scripts/fetch_monthly_all.py      # monthly series, all 10 CA DMAs -> data/food_bank_trends_california_dma_monthly.csv
python scripts/fetch_monthly_sparse.py   # diagnostic: the 3 low-volume DMAs (diagnostic; its output CSV was removed from the repo, not read by embed_data.py)
python scripts/fetch_us_states.py        # monthly series, all 50 states + DC -> data/food_bank_trends_us_states_monthly.csv
python scripts/embed_data.py             # rebuild the `const DATA = {...}` block inside index.html from the CSVs in data/
python scripts/probe_geo.py              # ad-hoc probe of which geo/breakdown-resolution combos the API accepts
python scripts/probe_state_ts.py         # ad-hoc probe of state-level (ADMINISTRATIVE_AREA1) time series
```

Fetch scripts **overwrite** their CSV wholesale (mode `w`) — they don't append, so a failed DMA mid-run leaves that DMA out of the file entirely. Watch the per-geo `ERROR`/`0 non-zero` lines they print.

Dashboard refresh workflow: run `fetch_monthly_all.py`, then always `embed_data.py` last to re-patch `index.html`. Open `index.html` directly in a browser — no server needed.

Auth: `.env` (gitignored, `key=value`, no quoting) holds `client_id`, `client_secret` (Google OAuth installed-app client) and `key` (used ad hoc). Token cache is `token.json`; `auth_state.json` and `hungertrends-*.json` (service-account key) are also gitignored.

## Trends API conventions

All fetch scripts follow the same shape (`docs.md` is a local copy of the Google API docs):

- POST `{BASE}:fetchTimeSeries` returns a long-running operation; poll `GET {BASE}/operations/{name}` until `done` (helpers cap at ~30 tries × 2s), then read `response.timeSeries.points`.
- `end_time` is always `now - 3 days` — the API's most recent days are unreliable. Points carry `isPartial`; it's persisted to CSV as `is_partial`.
- Geo selectors: DMA work uses `GEO_TYPE_DMA` with numeric codes; state work uses `GEO_TYPE_ADMINISTRATIVE_AREA1` with `US-XX` codes. `probe_geo.py` / `probe_state_ts.py` exist because not every geo × resolution combination is accepted.
- Windows: DMA scripts start at 2024-01-01; `fetch_us_states.py` uses a rolling 1795-day lookback (~5 years, near the API's limit).
- Every point has both `search_interest` (raw) and `scaled_search_interest` (0–100, scaled by the API). **`embed_data.py` renders only the scaled value.**

Three DMAs — Bakersfield `800`, Chico-Redding `813`, Santa Barbara `868` — have low query volume and return many zero/missing periods. They're flagged `sparse: true` in the embedded data and excluded from averages via `nz = [v for v in vals if v > 0]`. The same zero-inflation shows up at the state level for small states (see `data/term_validation_sparse_states.json`).

## Architecture

**`embed_data.py` is the single source of truth for what ends up on the page.** It:
1. Reads exactly two files — `data/food_bank_trends_california_dma.csv` (weekly) and `data/food_bank_trends_california_dma_monthly.csv`. No other CSV in `data/` reaches the dashboard.
2. Computes per-DMA stats (rolling avg, current value, YoY = last 12 non-zero months vs prior 12) and a statewide aggregate (average across DMAs per period, zeros excluded).
3. Serializes everything into one `DATA` JSON object and regex-replaces the `const DATA = {...};` block inside `index.html` in place — it does not regenerate the surrounding HTML/CSS/JS, only the data literal. DMA coordinates (`cx`/`cy`) are hand-projected lon/lat onto a 300×400 viewBox via `cx()`/`cy()` helpers that must stay consistent with the map SVG in `index.html`.

**`index.html`** is self-contained (HTML+CSS+JS, no external deps, no build tooling) with tabs for weekly vs. monthly views. It renders a canvas hero chart of the statewide aggregate, an SVG bubble map of DMAs sized by volume, a ranked list, and a small-multiples sparkline grid — all driven by properties read off the embedded `DATA` object at render time. Edit chart/interaction logic in the JS inside `index.html`; edit what data that JS can see in `embed_data.py`, then rerun it.

**Validation data** (`data/`, all untracked, produced ad hoc — there is no script in the repo that generates these; regenerating them means writing new code):
- `hps_raw/*.xlsx` — raw Census HPS week/cycle workbooks, 2021 wk30 → 2024 cycle09 (~22 MB, not gitignored).
- `hps_food_insufficiency_state.csv` — the flattened extract: `period, end_date, state_code, pct_insufficient, total_reporting`, 42 periods × 51 states. This is the ground-truth series to correlate search interest against.
- `term_validation_national.json` — national monthly `raw`/`scaled` series for five candidate terms ("food bank", "foodbank", "food pantry", "food bank near me", "food bank donation"), for choosing which query to track.
- `term_validation_sparse_states.json` — the same comparison for WY/VT/MT, to see which term survives in low-volume geos.

**Legacy/superseded scripts** — present from the first commit, not part of the current pipeline: `scripts/legacy/food_bank_trends.py` (weekly-only fetch, writes CSV to repo root not `data/`), `scripts/legacy/build_dashboard.py` and `scripts/legacy/build_dashboard_data.py` (generate a standalone `hunger_signal_dashboard.html`/stats print with only weekly data, no tabs), `scripts/legacy/sample.py` (Google's Flask OAuth example, verbatim). Don't extend these — extend `embed_data.py` and the `fetch_*` scripts instead. Note that `data/food_bank_trends_california_dma.csv` (the weekly file `embed_data.py` depends on) has no current producer script; it was moved into `data/` by hand.

`embedded_data.json` is a gitignored intermediate scratch file, not consumed by `index.html`.
