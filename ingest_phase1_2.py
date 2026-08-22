"""
Script de expansão Phase 1 + Phase 2: adiciona 5 competições/épocas
inteiras da StatsBomb Open Data ao dataset existente.

Reutiliza o pipeline existente sem alterações: `load_competition_events`
e `build_gk_events`/`build_gk_passes` (data_loader.py) e `ingest()`
(db/ingest.py) -- exatamente as mesmas funções que `download_extended_data.py`
e `ingest_performances.py` já usam. Não introduz nenhuma lógica de
agregação, cálculo ou persistência nova.

Processa uma competição de cada vez (download -> ingest -> commit) em vez
de acumular tudo em memória antes de gravar, por duas razões: (1) mantém o
pico de RAM controlado (cada competição tem até 380 jogos, ~1.5GB de
eventos, em vez de ~9GB de tudo junto), e (2) se uma competição falhar a
meio, as anteriores já ficam persistidas em vez de se perder tudo.

No fim, junta os eventos novos ao data/events_extended.pkl existente, para
que uma releitura futura desse ficheiro (ex.: correr ingest_performances.py
do zero) já inclua as 5 competições novas.

Corre com:
    python ingest_phase1_2.py
"""

import os

import pandas as pd
from sqlalchemy import create_engine

import _bootstrap  # noqa: F401  (coloca src/ no sys.path)

from gk_scouting.data_loader import build_gk_events, build_gk_passes, load_competition_events
from gk_scouting.db.config import get_database_url
from gk_scouting.db.ingest import ingest

EVENTS_PATH = os.path.join("data", "events_extended.pkl")

# IDs verificados ao vivo contra o catálogo StatsBomb
# (raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json)
# imediatamente antes de correr este script -- ver relatório da fase de
# auditoria para o número de jogos disponíveis em cada uma.
TARGETS = [
    (11, 27, "La Liga", "2015/2016"),
    (2, 27, "Premier League", "2015/2016"),
    (12, 27, "Serie A", "2015/2016"),
    (7, 27, "Ligue 1", "2015/2016"),
    (43, 3, "FIFA World Cup", "2018"),
]


def main() -> None:
    engine = create_engine(get_database_url())

    new_chunks = []

    for competition_id, season_id, competition_name, season_name in TARGETS:
        print("=" * 70)
        print(f"{competition_name} — {season_name} (competition_id={competition_id}, season_id={season_id})")
        print("=" * 70)

        events = load_competition_events(competition_id=competition_id, season_id=season_id)
        events["competition_id"] = competition_id
        events["season_id"] = season_id
        events["competition_name"] = competition_name
        events["season_name"] = season_name

        n_matches = events["match_id"].nunique()
        print(f"OK — {len(events):,} eventos, {n_matches:,} jogos")

        gk_events = build_gk_events(events)
        gk_passes = build_gk_passes(events)

        with engine.begin() as connection:
            count = ingest(events, gk_events, gk_passes, connection)
        print(f"{count} performances upsertadas para {competition_name} {season_name}.")

        new_chunks.append(events)

    print("\n" + "=" * 70)
    print("A atualizar data/events_extended.pkl com as competições novas...")
    print("=" * 70)

    if os.path.exists(EVENTS_PATH):
        existing = pd.read_pickle(EVENTS_PATH)
        combined = pd.concat([existing, *new_chunks], ignore_index=True)
    else:
        combined = pd.concat(new_chunks, ignore_index=True)

    combined.to_pickle(EVENTS_PATH)
    print(f"data/events_extended.pkl atualizado: {len(combined):,} eventos, "
          f"{combined['match_id'].nunique():,} jogos no total.")


if __name__ == "__main__":
    main()
