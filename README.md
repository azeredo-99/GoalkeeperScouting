# Goalkeeper Scouting 🧤⚽

> A data-driven scouting platform focused entirely on goalkeepers — real event data, real statistical benchmarking, and explainable scouting preferences instead of a black-box rating.

This is a personal portfolio project. It's built on free, open football data (StatsBomb Open Data) and is deliberately designed to be **transparent**: every number you see is traceable to a metric, a sample size, and a real comparison group. There is no single "goalkeeper score."

---

## What is this?

Goalkeepers are the most under-analysed position in football analytics — most tools are built around outfield and attacking stats. Goalkeeper Scouting tries to fix that, following a scout's actual workflow:

**Discover** candidates → **Profile** a goalkeeper in context → **Benchmark** them against real peers → find **Similar** goalkeepers → match against a **Scouting Profile** → **Shortlist** and add notes → generate a print-ready **Scouting Report**.

Everything is computed from raw StatsBomb match events — saves, sweeper actions, passes — not pre-aggregated stats from someone else's site.

---

## See it in action

Here's a walkthrough of a real scouting session, screenshotted straight from the running app against the live dataset.

### 1. Start on Discover

Search for a specific goalkeeper by name, or switch to "Discover by profile" to filter by competition, season, age, market value, minutes and performance thresholds.

![Discover — search](docs/screenshots/discover-search.png)

### 2. Open a Player Profile

Everything about one goalkeeper, in one specific competition/season sample — market context, a performance snapshot, plain-language takeaways, and a peer-group benchmark with real percentiles (never a global "how good is this keeper" score).

![Player Profile](docs/screenshots/player-profile.png)

### 3. Find Similar Goalkeepers

Adjustable-weight style similarity across Shot Stopping, Distribution and Proactivity, with a short explanation of what's closest and what differs between two players. Clearly labelled as model output, not a scout's judgement.

![Similar Goalkeepers](docs/screenshots/similar-goalkeepers.png)

### 4. Or start from what you're looking for: Scouting Profiles

Instead of a reference player, define what you actually want — a **High-Line Sweeper**, a **Possession Goalkeeper**, a **Young Prospect** — as a set of weighted preferences with minimums/maximums. This is scout-defined criteria, never a rating.

![Scouting Profiles](docs/screenshots/scouting-profiles.png)

### 5. Discover, matched against that profile

Turn the profile filter on and every result gets a **Scouting Match** badge — matched / unmet / insufficient-data counts, plus an optional, secondary, explainable match percentage. Missing data is never treated as a poor match.

![Discover with Scouting Match](docs/screenshots/discover-scouting-match.png)

### 6. Shortlist and annotate

Save candidates, set priority and status, and add scout notes — kept visibly separate from the statistical evidence above them.

![Shortlist](docs/screenshots/shortlist.png)

### 7. Generate the Scouting Report

A single, print-ready page combining the snapshot, takeaways, full metric breakdown, benchmark, similar goalkeepers and scout notes for one player/context — ready to hand to someone else.

![Scouting Report](docs/screenshots/scouting-report.png)

### 8. And know exactly how much to trust it

The Data Coverage page shows, per competition/season, how many goalkeepers the system actually has and how many clear the benchmarking threshold — no invented numbers, no hiding a thin sample.

![Data Coverage](docs/screenshots/data-coverage.png)

---

## Data

**[StatsBomb Open Data](https://github.com/statsbomb/open-data)** is the performance source — free, event-level football data (every pass, shot, and goalkeeper action, located on the pitch). Every metric in this project is derived directly from those raw events, not taken pre-calculated from anywhere.

**Transfermarkt** supplies market value, age, and current club — kept deliberately separate from performance data, so a player's market status never leaks into their statistical sample.

**Not used:** SofaScore, FotMob, Flashscore, WhoScored, and FBref were all investigated as potential current-season sources. None are scraped or integrated — each has explicit terms-of-service language against automated collection, which isn't compatible with a public project. This project trades broader coverage for a source that's free and legally unambiguous.

## Methodology

- **Shot Stopping** — save %, shots faced/saved, goals conceded (shots that never forced a save are excluded from the save-% denominator)
- **Sweeping / Proactivity** — sweeper actions /90, average and max distance from goal for those actions
- **Distribution** — pass success %, average pass length, long-ball %

Minutes are computed from real lineup/substitution/red-card events, not estimated. A metric with no underlying events is shown as missing, never as `0`. Sample size is always visible next to every stat — the app tells you when a percentage is based on 3 shots vs. 30.

**Performance Benchmark** compares a goalkeeper only against peers in the *same competition and season* (≥450 minutes by default), using percentile rank with tie handling. **Similarity** uses robust z-scores and a weighted exponential-decay function across six style metrics. **Scouting Match** evaluates one player, in one context, against one profile's preferences — always `matched` / `unmet` / `insufficient_data`, never a combined score presented as fact.

## Tech Stack

**Backend** — Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, pandas, [`statsbombpy`](https://pypi.org/project/statsbombpy/)
**Frontend** — React 19, TypeScript, Vite
**Data** — StatsBomb Open Data, Transfermarkt
**Testing** — pytest (244 tests), TypeScript build checks

## Dataset

| | |
|---|---|
| Goalkeeper-performance rows | **410** |
| Unique players | **330** |
| Competition/season contexts | **13** |
| Contexts with strong statistical coverage | **4** |

| Competition | Season | Goalkeepers | Benchmarkable (≥450min) | Coverage |
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

The four "strong" contexts are all full **2015/16 season** releases from StatsBomb (380 matches for La Liga/Premier League/Serie A, 377 for Ligue 1) — the only samples in this dataset large enough to give every regular starter a genuine full-season peer group.

**Important limitation:** StatsBomb Open Data is a static, historical release — not a continuously updated current-season feed like SofaScore or Flashscore. Bundesliga and MLS are capped at what StatsBomb has actually published for those leagues (34 and 6 matches). Champions League Open Data is extremely sparse (one match per season).

## Local Setup

```bash
git clone https://github.com/azeredo-99/Goalkeeper-Scouting.git
cd Goalkeeper-Scouting

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

pip install -r requirements.txt
pip install fastapi "uvicorn[standard]"   # not yet pinned in requirements.txt

docker compose up -d
alembic upgrade head
# copy .env.example to .env and set DATABASE_URL first

python download_extended_data.py
python ingest_performances.py

uvicorn gk_scouting.api.main:app --app-dir src --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

```bash
pytest
```

## Limitations

- No current-season data source — see above.
- Player identity currently uses `(player_name, competition_id, season_id)` as the database key, not StatsBomb's stable `player_id`. The most recent audit found zero same-context name collisions across 330 players, but this is a structural risk that grows with the dataset.
- Custom Scouting Profiles created in the UI live in browser storage only — server-side Discover matching currently supports just the three built-in profiles.
- Portfolio project — no authentication, no multi-user support, no production deployment.

## Roadmap

**Done:** dataset expansion (5 competitions, 1,581 matches ingested), Player Profile, Scouting Report, Performance Benchmark, Similar Goalkeepers, Scouting Profiles & Scouting Match, Data Coverage, Shortlist with scout notes.

**Next:** a `player_id`-based identity model, a legally-usable current-season source (if one exists), deeper historical StatsBomb coverage, and wiring custom profiles into server-side matching.

---

## Author

**Guilherme Azeredo** — Computer Systems Engineering graduate interested in software development, data, and football analytics.

[GitHub](https://github.com/azeredo-99) · [LinkedIn](https://www.linkedin.com/in/guilherme-azeredo-a11bb0254/)

## License / Data Attribution

For educational and portfolio purposes. StatsBomb Open Data is used under StatsBomb's public data terms — published analysis should credit StatsBomb ([media pack](https://statsbomb.com/media-pack/)). Transfermarkt data is subject to Transfermarkt's own terms.
