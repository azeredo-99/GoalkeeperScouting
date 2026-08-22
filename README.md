# Goalkeeper Scouting

A goalkeeper-focused data scouting platform built on real, open football data — combining performance metrics, statistical benchmarking, player profiles, similarity search, scout-defined preferences, and a shortlist/report workflow.

This is a portfolio/CV project. It is explicitly **not** an opaque AI ranking system: every number shown is traceable to a metric, a sample size, and a comparison context. There is no single "goalkeeper score."

---

## Table of Contents

- [Overview](#overview)
- [Why Goalkeeper Scouting](#why-goalkeeper-scouting)
- [Key Features](#key-features)
- [Data](#data)
- [Methodology](#methodology)
- [Scouting Profiles & Scouting Match](#scouting-profiles--scouting-match)
- [Architecture](#architecture)
- [Dataset / Coverage](#dataset--coverage)
- [API](#api)
- [Testing](#testing)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Local Setup](#local-setup)
- [Project Structure](#project-structure)
- [License / Data Attribution](#license--data-attribution)

---

## Overview

Goalkeeper Scouting ingests StatsBomb's free, open event-level football data, derives goalkeeper-specific performance metrics from the raw events (shot stopping, sweeping/proactivity, distribution), and exposes them through a React + FastAPI application built around a real scouting workflow:

**Discover** candidates → **Profile** a goalkeeper in context → **Benchmark** them against real peers → find **Similar** goalkeepers → optionally match against a **Scouting Profile** → **Shortlist** and annotate → generate a print-ready **Scouting Report**.

## Why Goalkeeper Scouting

Goalkeepers are chronically underserved by mainstream football analytics, which is built almost entirely around outfield/attacking metrics. This project exists to explore what a genuinely goalkeeper-first analytics tool looks like — and to do so on a data source (StatsBomb Open Data) that is free, legally unambiguous, and public, rather than scraping commercial sites.

The project also deliberately favours **explainability over sophistication**: peer-group percentiles instead of a black-box rating, preference matching instead of a single "fit score," and clear "insufficient data" states instead of silently treating missing data as poor performance.

## Key Features

- **Discover** — search a specific goalkeeper by name, or filter candidates by competition/season, age, market value, minutes, and performance thresholds.
- **Player Profile** — a goalkeeper's identity, current market context, and a detailed performance breakdown for one specific competition/season sample.
- **Performance Benchmark** — percentile comparison against real peers in the same competition/season, with sample size and coverage tier always visible.
- **Similar Goalkeepers** — a style-similarity search across shot-stopping, distribution, and proactivity, with a short explanation of what's closest and what differs.
- **Scouting Profiles & Scouting Match** — scout-defined preferences (not a rating) evaluated against a goalkeeper's real data, with matched/unmet/insufficient-data states.
- **Shortlist** — save goalkeepers, set priority/status, add scout notes, and view a live Scouting Match against a chosen profile.
- **Scouting Report** — a print-ready, single-page report combining all of the above for one player/context.
- **Data Coverage** — an internal view of exactly what the system knows, per competition/season, with no invented numbers.

## Data

### StatsBomb Open Data — performance source

[StatsBomb Open Data](https://github.com/statsbomb/open-data) provides free, event-level football data (every pass, shot, goalkeeper action, located on the pitch). This project downloads it via the [`statsbombpy`](https://pypi.org/project/statsbombpy/) client and derives every goalkeeper metric directly from raw events — nothing is taken as a pre-aggregated statistic from a third party.

### Transfermarkt — identity & market context

Player market value, age, and current club come from Transfermarkt data, kept deliberately **separate** from performance data: a player's market status is never mixed into their statistical sample.

### Sources investigated but not integrated

SofaScore, FotMob, Flashscore, WhoScored, and FBref were evaluated for current-season goalkeeper coverage. None are scraped or integrated: each has explicit terms-of-service language prohibiting automated collection, which is incompatible with a public portfolio project. This project prioritizes legally clear, reproducible open data over broader but legally risky coverage. See [Limitations](#limitations) for the practical consequence of this choice.

## Methodology

All metrics are computed in [`metrics.py`](src/gk_scouting/metrics.py) directly from StatsBomb events — nothing is sourced pre-calculated. Minutes are computed from actual lineup/substitution/red-card events (regulation time only; stoppage time is absorbed into the period boundary), not estimated from event presence.

**Shot Stopping**
- `save_pct` — saves ÷ shots on target (shots that never forced a save are excluded from the denominator; `NaN`, not 0%, when a keeper faced no shots on target)
- `shots_faced`, `shots_saved`, `goals_conceded`, `shots_faced_p90`

**Sweeping / Proactivity**
- `sweeper_actions`, `sweeper_actions_p90` — actions tagged `Keeper Sweeper` by StatsBomb
- `avg_distance_from_goal`, `max_distance_from_goal` — distance of those actions from the player's own goal

**Distribution**
- `total_passes`, `pass_success_pct`, `avg_pass_length`, `long_ball_pct` (passes over 40m)

**Sample size is treated as a first-class value.** `minutes` is always shown alongside every metric, and the UI explicitly labels small samples rather than presenting every percentage as equally reliable. A metric with no underlying events (e.g. a keeper who never left the box) is `null`, never `0`.

### Performance Benchmark

`build_benchmark()` (in [`benchmarking.py`](src/gk_scouting/benchmarking.py)) compares a goalkeeper against **peers in the same competition and season only** — never a global population, never mixed contexts. The peer pool default is **≥450 minutes**. Percentiles use average-rank tie handling and are computed with no external statistics dependency. Per-metric status is `no_data`, `insufficient` (<5 peers), `small` (5–9 peers), or `normal` (10+ peers).

### Similar Goalkeepers

[`similarity_engine.py`](src/gk_scouting/similarity_engine.py) computes similarity across three dimensions — **Shot Stopping**, **Distribution**, **Proactivity** — built from six underlying metrics (save %, pass success %, avg. pass length, long-ball %, sweeper actions/90, avg. distance from goal). Each metric is converted to a robust z-score (median/IQR-based, resistant to outliers), combined via a weighted exponential-decay similarity function, and default-weighted 30/35/35 across the three dimensions. Eligibility requires a minimum-minutes threshold (defaulting to the 25th percentile of the pool, rounded down to a multiple of 90). The result is explicitly presented as **model-based output**, not a scout's judgement, with a short generated explanation of the closest and most different metric between two players.

## Scouting Profiles & Scouting Match

A **Scouting Profile** ([`scouting_profiles.py`](src/gk_scouting/scouting_profiles.py)) is a named set of scout preferences — never a player rating. Each preference is `metric + enabled + weight + optional minimum/maximum`. Three built-in profiles ship with the API:

| Profile | Idea |
|---|---|
| **High-Line Sweeper** | Proactive sweeper-keeper suited to a high defensive line |
| **Possession Goalkeeper** | Reliable short distribution, comfortable building from the back |
| **Young Prospect** | Younger goalkeeper with a workable sample and development runway |

**Scouting Match** ([`scouting_match.py`](src/gk_scouting/scouting_match.py)) evaluates one player, in one competition/season context, against one profile — always **PLAYER × PROFILE × CONTEXT**, never a stored or context-independent score. Every preference resolves to exactly one of three states:

- `matched` — value present and within range
- `unmet` — value present but outside range
- `insufficient_data` — no value for this player/context — **never treated as `unmet`**

An optional `matchScore` (weighted share of matched preferences, ignoring missing data in the denominator) is exposed as a secondary, explainable number — never presented alone.

Scouting Match is integrated into **Discover** (opt-in profile filter, match badges on results, "Sort by Scouting Match"), **Shortlist** (per-session profile selector, live per-player match), and **Scouting Report** (match evidence + a deterministic, template-generated "Questions to investigate" list — no generated prose, every line traces to a real value).

**Known limitation:** custom or duplicated profiles created via the `/scouting-profiles` page are stored in browser `localStorage` only. Only the three built-in profiles are wired into server-side Discover matching today.

## Architecture

```
StatsBomb Open Data (statsbombpy)
        │
        ▼
data_loader.py       → download match events, extract GK events/passes
        │
        ▼
metrics.py            → build_scouting_table(): aggregate raw events into
        │                one row per (player, competition, season)
        ▼
db/ingest.py           → INSERT ... ON CONFLICT DO UPDATE into gk_performances
        │                (idempotent — safe to rerun)
        ▼
PostgreSQL              → gk_performances (composite PK: player_name,
                           competition_id, season_id)
        │
        ▼
FastAPI (api/main.py)   → reads the table once at startup, serves
        │                 discovery/benchmark/similarity/scouting-match/coverage
        ▼
React + TypeScript      → Discover, Player Profile, Compare, Similar,
                           Shortlist, Scouting Report, Scouting Profiles,
                           Data Coverage
```

The primary key of `gk_performances` is currently `(player_name, competition_id, season_id)` — a name string, not StatsBomb's stable numeric `player_id`. See [Limitations](#limitations).

### A note on the most recent ingestion (Phase 1 + 2)

Five full competitions/seasons (1,581 matches total) were added in the most recent expansion. To stay within memory and execution-time limits, each competition's matches were **downloaded in chunks to disk**, but the aggregation step (`build_scouting_table` → `ingest()`) was run **exactly once per competition, over the fully combined event set** — not once per chunk. An earlier attempt that aggregated and upserted per chunk produced a real bug: because the database upsert *replaces* a row rather than merging it, any goalkeeper whose matches were split across chunks ended up with only their last-ingested chunk's partial-season stats. This was caught before being reported as complete, and fixed by separating "download" from "aggregate" into two distinct steps. The production ingestion pipeline itself (`data_loader.py`, `db/ingest.py`) does not chunk internally — this was a reliability practice for a one-off large download, not a permanent code change.

## Dataset / Coverage

As of the most recent ingestion:

| | Value |
|---|---|
| Goalkeeper-performance rows | **410** |
| Unique players | **330** |
| Competition/season contexts | **13** |
| Contexts rated "strong" coverage | **4** |
| Duplicate `(player_name, competition_id, season_id)` keys | **0** |
| Same-context player-name → multiple StatsBomb `player_id` collisions | **0** (audited across the 5 newly-added contexts) |

Coverage status (from [`data_coverage.py`](src/gk_scouting/data_coverage.py)) is based on how many goalkeepers in a context clear the 450-minute benchmarking threshold: **strong** (10+), **partial** (5–9), **limited** (1–4), **insufficient** (0).

| Competition | Season | Goalkeepers | Benchmarkable (≥450min) | Status |
|---|---|---:|---:|---|
| Ligue 1 | 2015/2016 | 46 | 33 | Strong |
| Premier League | 2015/2016 | 48 | 32 | Strong |
| La Liga | 2015/2016 | 45 | 31 | Strong |
| Serie A | 2015/2016 | 48 | 26 | Strong |
| FIFA World Cup | 2018 | 41 | 8 | Partial |
| FIFA World Cup | 2022 | 41 | 7 | Partial |
| UEFA Euro | 2024 | 29 | 7 | Partial |
| African Cup of Nations | 2023 | 31 | 7 | Partial |
| La Liga | 2020/2021 | 23 | 2 | Limited |
| Ligue 1 | 2022/2023 | 25 | 1 | Limited |
| 1. Bundesliga | 2023/2024 | 23 | 1 | Limited |
| Major League Soccer | 2023 | 8 | 1 | Limited |
| Champions League | 2018/2019 | 2 | 0 | Insufficient |

The four "strong" contexts are all full **2015/16 season** releases from StatsBomb (380 matches for La Liga/Premier League/Serie A, 377 for Ligue 1) — StatsBomb's well-known complete free-data seasons. They're disproportionately valuable here because they're the only contexts in this dataset large enough to give every regular starter a genuine full-season sample, producing real statistical peer groups (26–33 comparable goalkeepers) instead of the 1–8 peers typical of the tournament/partial-season contexts.

**Important limitation:** StatsBomb Open Data is a static, historical release — it does not provide a continuously updated current-season goalkeeper dataset comparable to commercial live sources (SofaScore, Flashscore, FotMob). Bundesliga and MLS are capped at what StatsBomb has released for those competitions (34 and 6 matches respectively — no larger season exists in Open Data to ingest). Champions League Open Data is extremely sparse (one match per season across 15 available seasons).

## API

Backend: FastAPI, serving JSON, CORS-open for local development. All endpoints are `GET`. Exact routes (from [`api/main.py`](src/gk_scouting/api/main.py)):

| Endpoint | Purpose |
|---|---|
| `/api/competitions` | Competitions actually present in the ingested data |
| `/api/seasons?competition_id=` | Seasons present (optionally scoped to a competition) |
| `/api/players/search?q=` | Name search |
| `/api/players/discover` | Filtered candidate search (competition/season/age/value/minutes/performance thresholds, optional `scouting_profile_id`) |
| `/api/players/{player_name}/performances` | A player's identity + all performance contexts |
| `/api/players/{player_name}/benchmark?competition_id=&season_id=` | Peer-group percentile benchmark |
| `/api/players/{player_name}/scouting-match?profile_id=&competition_id=&season_id=` | Scouting Match for one player/profile/context |
| `/api/scouting-profiles` | List built-in scouting profiles |
| `/api/scouting-profiles/{profile_id}` | One profile's full preference set |
| `/api/data-coverage` | Per-context coverage (as tabulated above) |
| `/api/comparison?selections=name:competitionId:seasonId,...` | 2–4 player comparison table |
| `/api/similarity?target=&w_shot_stopping=&w_distribution=&w_proactivity=` | Similar-goalkeeper search |

## Testing

- **Backend:** 244 tests passed, 2 skipped (`pytest`), covering metrics, ingestion idempotency, benchmarking, similarity, discovery, comparison, scouting profiles/match, and data coverage.
- **Frontend:** TypeScript compiles clean (`tsc -b`), production build clean (`vite build`).
- **Browser QA:** Discover (search + filtered + profile modes), Player Profile, Benchmark, Similar Goalkeepers, Shortlist (with live Scouting Match), Scouting Report, Scouting Profiles, and Data Coverage were manually verified against the live API and real PostgreSQL data, including a tablet-width (768px) responsiveness check on Discover. No console errors found in the pages checked.

These numbers reflect the state at the time of writing and are not enforced by CI.

## Limitations

- **No current-season data source.** StatsBomb Open Data is historical/static; nothing in this project scrapes SofaScore, FotMob, Flashscore, WhoScored, or FBref, all of which were evaluated and found to have anti-automation terms incompatible with a public project.
- **Bundesliga and MLS coverage is capped at the source** (34 and 6 matches respectively) — not an ingestion limitation, StatsBomb has not released more for these competitions.
- **Champions League Open Data is extremely sparse** — one match per season across all 15 available seasons.
- **Player identity uses names, not stable IDs.** `gk_performances`'s primary key is `(player_name, competition_id, season_id)`. StatsBomb's numeric `player_id` exists in the raw events but is not currently persisted or used as the identity key. The most recent audit found **zero** same-context name collisions across 330 players, but this remains a structural risk that grows with dataset size — see [Roadmap](#roadmap).
- **Custom Scouting Profiles are local-only.** Profiles duplicated/edited via the UI live in browser `localStorage` and are not evaluated by the server-side Discover matching, which only supports the three built-in profiles.
- This is a portfolio project, not a production scouting tool. No authentication, no multi-user support, no deployment target.

## Roadmap

### Done
- Expanded dataset via Phase 1 + Phase 2 ingestion (5 competitions, 1,581 matches)
- Player Profile (header, market context, performance snapshot, takeaways, benchmark, evidence sections, radar, sweeper map, similar-goalkeeper preview, shortlist/compare actions, Scout Decision Area, report link)
- Scouting Report (print-ready, context-preserving, scout notes separated from statistical evidence)
- Performance Benchmark (peer-group percentiles, coverage-aware)
- Similar Goalkeepers (style similarity, explained)
- Scouting Profiles (3 built-in profiles)
- Scouting Match (Discover/Shortlist/Report integration)
- Data Coverage page
- Shortlist with priority/status/scout notes

### Future / not implemented
- `player_id`-based identity architecture (replacing the name-based primary key)
- A current-season data source, if one is found that is both free and legally usable
- Additional historical StatsBomb seasons (e.g. deeper La Liga back-catalog, UEFA Euro 2020, Copa América 2024)
- Ingestion performance work, if further large-scale expansion is pursued
- Wiring custom/duplicated Scouting Profiles into server-side Discover matching

## Local Setup

### Backend

```bash
git clone https://github.com/azeredo-99/Goalkeeper-Scouting.git
cd Goalkeeper-Scouting

python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
pip install fastapi "uvicorn[standard]"   # not yet pinned in requirements.txt
```

Start PostgreSQL and apply migrations:

```bash
docker compose up -d
alembic upgrade head
```

Copy `.env.example` to `.env` and set `DATABASE_URL` to match your local Postgres credentials, then ingest data:

```bash
python download_extended_data.py     # fetch StatsBomb events
python ingest_performances.py        # aggregate + upsert into gk_performances
```

Run the API:

```bash
uvicorn gk_scouting.api.main:app --app-dir src --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
pytest
```

## Project Structure

```
Goalkeeper-Scouting/
├── src/gk_scouting/
│   ├── api/main.py            # FastAPI app and all routes
│   ├── db/                    # SQLAlchemy models, repository, ingest, config
│   ├── metrics.py             # event → goalkeeper metric aggregation
│   ├── similarity_engine.py   # style-similarity search
│   ├── benchmarking.py        # peer-group percentile benchmark
│   ├── scouting_profiles.py   # scouting profile data model
│   ├── scouting_match.py      # player × profile × context matching
│   ├── data_coverage.py       # internal coverage view
│   ├── discovery.py           # search/filter logic
│   ├── comparison.py          # multi-player comparison
│   ├── presentation.py        # formatting helpers
│   └── data_loader.py         # StatsBomb download + GK event extraction
├── frontend/src/
│   ├── pages/                 # Discover, PlayerProfile, Compare, Similar,
│   │                          # Shortlist, ScoutingReport, ScoutingProfiles,
│   │                          # DataCoverage
│   ├── components/            # Benchmark, RadarChart, SweeperMap, etc.
│   └── lib/                   # shortlist store, takeaways, formatting
├── tests/                     # 17 test files, pytest
├── alembic/                   # database migrations
├── data/                      # local StatsBomb/Transfermarkt data (gitignored)
├── download_extended_data.py  # StatsBomb download entry point
├── ingest_performances.py     # aggregation + upsert entry point
├── main.py, streamlit_app.py  # original single-competition CLI/Streamlit
│                               # prototype, predates the React/FastAPI app
└── docker-compose.yml          # local PostgreSQL
```

## License / Data Attribution

This project is for educational and portfolio purposes.

- **StatsBomb Open Data** is used under StatsBomb's public data terms; published analysis based on this data should credit StatsBomb (see their [media pack](https://statsbomb.com/media-pack/)).
- **Transfermarkt** data is subject to Transfermarkt's own terms.

---

### Author

**Guilherme Azeredo** — Computer Systems Engineering graduate interested in software development, data, and football analytics.

[GitHub](https://github.com/azeredo-99) · [LinkedIn](https://www.linkedin.com/in/gui-azeredo-a11bb0254/)
