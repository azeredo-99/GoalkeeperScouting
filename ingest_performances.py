"""
Script de ingestão: lê data/events_extended.pkl, calcula
build_scouting_table(context_columns=CONTEXT_COLUMNS) (ver metrics.py,
inalterado) e faz upsert em gk_performances.

Corre com:
    python ingest_performances.py

Pré-requisitos:
    - PostgreSQL a correr com o schema já migrado
      (ver docker-compose.yml e alembic/);
    - DATABASE_URL definida no ambiente (ver .env.example).

Correr este script mais do que uma vez é seguro: gk_performances usa
INSERT ... ON CONFLICT DO UPDATE (ver gk_scouting.db.ingest), por isso
guarda-redes já existentes são atualizados, nunca duplicados.
"""

import os

import pandas as pd
from sqlalchemy import create_engine

import _bootstrap  # noqa: F401  (coloca src/ no sys.path)

from gk_scouting.data_loader import build_gk_events, build_gk_passes
from gk_scouting.db.config import get_database_url
from gk_scouting.db.ingest import ingest

EVENTS_PATH = os.path.join("data", "events_extended.pkl")


def main() -> None:
    if not os.path.exists(EVENTS_PATH):
        raise FileNotFoundError(
            f"{EVENTS_PATH} não encontrado. Este script precisa do dataset "
            "multi-competição (com competition_id/season_id) -- não "
            "funciona com events_full_wc2022.pkl, que é de uma só "
            "competição e não tem essas colunas."
        )

    print(f"A carregar {EVENTS_PATH}...")
    events = pd.read_pickle(EVENTS_PATH)
    gk_events = build_gk_events(events)
    gk_passes = build_gk_passes(events)

    engine = create_engine(get_database_url())

    with engine.begin() as connection:
        count = ingest(events, gk_events, gk_passes, connection)

    print(f"{count} performances upsertadas em gk_performances.")


if __name__ == "__main__":
    main()
