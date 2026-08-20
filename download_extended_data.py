"""Download the newest available male StatsBomb Open Data seasons."""

from pathlib import Path
import re

import pandas as pd
import requests

import _bootstrap  # noqa: F401  (coloca src/ no sys.path)

from gk_scouting.data_loader import load_competition_events

COMPETITIONS_URL = (
    "https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json"
)
OUTPUT = Path("data/events_extended.pkl")

# Names are matched flexibly because StatsBomb uses names such as
# "1. Bundesliga" and "Champions League" rather than our preferred labels.
PRIORITY_COMPETITIONS = [
    ("Premier League", ["premier league"]),
    ("La Liga", ["la liga"]),
    ("Bundesliga", ["bundesliga"]),
    ("Ligue 1", ["ligue 1"]),
    ("Serie A", ["serie a"]),
    ("Eredivisie", ["eredivisie"]),
    ("Primeira Liga", ["primeira liga"]),
    ("Champions League", ["champions league"]),
    ("Europa League", ["europa league"]),
    ("MLS", ["major league soccer", "mls"]),
    ("World Cup", ["fifa world cup"]),
    ("European Championship", ["uefa euro", "european championship"]),
    ("Copa America", ["copa america"]),
]


def load_catalog():
    response = requests.get(COMPETITIONS_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def season_year(season_name):
    """Return the latest year represented by a season name."""
    years = [int(x) for x in re.findall(r"\d{4}", str(season_name))]
    if years:
        return max(years)
    years = [int(x) for x in re.findall(r"\d{2}", str(season_name))]
    return max(years) if years else -1


def is_male_senior(row):
    return (
        str(row.get("competition_gender", "")).lower() == "male"
        and not bool(row.get("competition_youth", False))
    )


def find_candidates(catalog, aliases):
    aliases = [a.lower() for a in aliases]
    return [
        row
        for row in catalog
        if is_male_senior(row)
        and any(
            alias in str(row.get("competition_name", "")).lower()
            for alias in aliases
        )
    ]


def select_latest_competitions(catalog):
    """Select exactly the newest available season for each target competition."""
    selected = []

    for display_name, aliases in PRIORITY_COMPETITIONS:
        candidates = find_candidates(catalog, aliases)
        if not candidates:
            continue

        latest = max(
            candidates,
            key=lambda row: (
                season_year(row.get("season_name", "")),
                str(row.get("match_available", "")),
            ),
        )
        selected.append(latest)

    # Remove accidental duplicates by competition/season.
    unique = {}
    for row in selected:
        key = (row["competition_id"], row["season_id"])
        unique[key] = row

    return list(unique.values())


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GOALKEEPER SCOUTING — BASE EXTENDIDA")
    print("=" * 70)
    print("A consultar o catálogo atual do StatsBomb...")

    catalog = load_catalog()
    selected = select_latest_competitions(catalog)

    if not selected:
        raise RuntimeError("Não foram encontradas competições compatíveis.")

    print("\nÉpocas MAIS RECENTES realmente disponíveis:")
    for row in selected:
        print(
            f" - {row['competition_name']} | {row['season_name']} | "
            f"competition_id={row['competition_id']} | season_id={row['season_id']}"
        )

    datasets = []
    failed = []

    for i, row in enumerate(selected, start=1):
        competition_name = row["competition_name"]
        season_name = row["season_name"]
        print("\n" + "-" * 70)
        print(f"[{i}/{len(selected)}] {competition_name} — {season_name}")

        try:
            events = load_competition_events(
                competition_id=int(row["competition_id"]),
                season_id=int(row["season_id"]),
            )
            events["competition_id"] = int(row["competition_id"])
            events["season_id"] = int(row["season_id"])
            events["competition_name"] = competition_name
            events["season_name"] = season_name
            datasets.append(events)
            print(f"OK — {len(events):,} eventos")
            print(f"     {events['match_id'].nunique():,} jogos")
        except Exception as exc:
            print(f"ERRO — {exc}")
            failed.append(f"{competition_name} — {season_name}")

    if not datasets:
        raise RuntimeError("Não foi possível descarregar nenhuma competição.")

    all_events = pd.concat(datasets, ignore_index=True)
    all_events.to_pickle(OUTPUT)

    goalkeeper_events = all_events[all_events["type"] == "Goal Keeper"]

    print("\n" + "=" * 70)
    print("BASE CRIADA COM SUCESSO")
    print("=" * 70)
    print(f"Ficheiro: {OUTPUT}")
    print(f"Eventos: {len(all_events):,}")
    print(f"Jogos: {all_events['match_id'].nunique():,}")
    print(f"Eventos de GR: {len(goalkeeper_events):,}")

    summary = (
        all_events.groupby(["competition_name", "season_name"])
        .agg(jogos=("match_id", "nunique"), eventos=("match_id", "size"))
        .sort_values("jogos", ascending=False)
    )
    print("\nPor competição:")
    print(summary.to_string())

    if failed:
        print("\nCompetições que falharam:")
        for name in failed:
            print(f" - {name}")


if __name__ == "__main__":
    main()
