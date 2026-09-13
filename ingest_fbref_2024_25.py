"""
Ingestão dos dados de guarda-redes do FBref (época 2024/25, big-5 ligas)
em `gk_performances`, com `source="fbref"`.

Reutiliza a mesma máquina de upsert idempotente do StatsBomb
(`gk_scouting.db.ingest.table_to_records` / `build_upsert_statement`) --
não introduz uma segunda pipeline de escrita. `metrics.py` não é tocado:
esta fonte já vem agregada por jogador pela própria FBref, não há
eventos brutos para processar.

Pré-requisito: correr `fetch_fbref_gk_2024_25.py` primeiro (fora desta
pipeline -- ver aviso nesse ficheiro sobre os Termos de Uso da FBref) e
ter os 5 CSVs em data/raw/fbref/2024-25/.

Corre com:
    python ingest_fbref_2024_25.py
"""

import pandas as pd
from sqlalchemy import create_engine

import _bootstrap  # noqa: F401  (coloca src/ no sys.path)

from gk_scouting.db.config import get_database_url
from gk_scouting.db.ingest import build_upsert_statement, table_to_records
from gk_scouting.fbref_mapping import (
    FBREF_COMPETITIONS,
    aggregate_multi_club_rows,
    build_fbref_table,
    load_all_raw_keeper_csvs,
)

RAW_DIR = "data/raw/fbref/2024-25"


def main() -> None:
    print("=" * 70)
    print("FBref 2024/25 — leitura dos CSVs")
    print("=" * 70)

    raw = load_all_raw_keeper_csvs(RAW_DIR)
    print(f"Linhas brutas lidas (todas as ligas): {len(raw)}")

    multi_club_counts = (
        raw.groupby(["league", "season", "player"])["team"]
        .nunique()
    )
    multi_club_players = multi_club_counts[multi_club_counts > 1]
    print(f"Jogadores com múltiplos clubes na época (agregados numa só linha): {len(multi_club_players)}")
    for (league, season, player), n_teams in multi_club_players.items():
        print(f"  - {player} ({league}): {n_teams} clubes")

    aggregated = aggregate_multi_club_rows(raw)
    print(f"Linhas após agregação multi-clube: {len(aggregated)}")

    table = build_fbref_table(RAW_DIR)
    print(f"Registos preparados para gk_performances: {len(table)}")

    print("\nDistribuição por competição:")
    for league, (competition_id, name) in FBREF_COMPETITIONS.items():
        n = (table.index.get_level_values("competition_id") == competition_id).sum()
        print(f"  - {name} (competition_id={competition_id}): {n} guarda-redes")

    records = table_to_records(table)
    statement = build_upsert_statement(records)

    engine = create_engine(get_database_url())
    with engine.begin() as connection:
        result = connection.execute(statement)
        upserted = result.rowcount

    print("\n" + "=" * 70)
    print(f"{upserted} registos upsertados em gk_performances (source=fbref).")
    print("=" * 70)


if __name__ == "__main__":
    main()
