"""
Dataset sintético determinístico para os testes de baseline.

Substitui os pickles de eventos (286 MB / 1,3 GB) por um conjunto mínimo de
eventos construído à mão, com valores escolhidos para que todas as métricas
esperadas possam ser calculadas de cabeça e auditadas no próprio teste.

Reproduz a estrutura real do StatsBomb no que importa para os minutos:

* um evento `Starting XI` por equipa, com `tactics.lineup`;
* `Substitution` com `player` (sai) e `substitution_replacement` (entra);
* coluna `period`, com o relógio a reiniciar no início regulamentar de
  cada período (1 → 0, 2 → 45, 3 → 90, 4 → 105).

Estrutura (3 jogos, 4 guarda-redes):

    Jogo 1 — termina no período 2  → 90 minutos regulamentares
        Keeper A (Team X) : titular, jogo completo          →  90'
        Keeper B (Team Y) : titular, jogo completo          →  90'

    Jogo 2 — termina no período 4  → 120 minutos (prolongamento)
        Keeper A (Team X) : titular, sem substituição       → 120'

    Jogo 3 — termina no período 2  → 90 minutos
        Keeper C (Team Z) : titular, substituído aos 60'    →  60'
        Keeper D (Team Z) : entra aos 60'                   →  30'

Totais: A = 210', B = 90', C = 60', D = 30'.

Os eventos de remate, passe e saída de cada guarda-redes são exatamente os
mesmos de antes do P0-2, para que as métricas independentes de minutos
continuem a ter os mesmos valores esperados.
"""

import pandas as pd
import pytest

from gk_scouting.data_loader import build_gk_events, build_gk_passes
from gk_scouting.metrics import build_scouting_table


# As localizações formam triângulos 3-4-5 a partir da baliza própria (0, 40),
# para que as distâncias sejam exatas e verificáveis à mão.
SWEEPER_LOCATIONS = [
    ([3.0, 44.0], 5.0),    # hypot(3, 4)  = 5
    ([6.0, 48.0], 10.0),   # hypot(6, 8)  = 10
]


EVENT_COLUMNS = [
    "type", "match_id", "period", "minute", "second", "player", "team",
    "position", "goalkeeper_type", "goalkeeper_outcome", "location",
    "pass_outcome", "pass_length", "pass_end_location", "pass_height",
    "pass_body_part", "pass_type", "tactics", "substitution_replacement",
    "substitution_outcome", "foul_committed_card", "bad_behaviour_card",
]


def _blank(**overrides):
    row = {column: None for column in EVENT_COLUMNS}
    row["second"] = 0
    row.update(overrides)
    return row


def starting_xi(match_id, team, lineup):
    """
    Evento `Starting XI`.

    `lineup` é uma lista de (nome, posição). No StatsBomb real são sempre
    exatamente 11 entradas; aqui usamos menos para manter a fixture legível,
    porque o cálculo de minutos só depende de quem lá está, não de quantos.
    """
    return _blank(
        type="Starting XI",
        match_id=match_id,
        period=1,
        minute=0,
        team=team,
        tactics={
            "formation": 442,
            "lineup": [
                {
                    "player": {"id": 1000 + index, "name": name},
                    "position": {"id": 1, "name": position},
                    "jersey_number": index + 1,
                }
                for index, (name, position) in enumerate(lineup)
            ],
        },
    )


def substitution(match_id, period, minute, team, player_off, player_on):
    return _blank(
        type="Substitution",
        match_id=match_id,
        period=period,
        minute=minute,
        team=team,
        player=player_off,
        position="Goalkeeper",
        substitution_replacement=player_on,
        substitution_outcome="Tactical",
    )


def gk_event(match_id, period, minute, player, team, gk_type, location=None):
    return _blank(
        type="Goal Keeper",
        match_id=match_id,
        period=period,
        minute=minute,
        player=player,
        team=team,
        position="Goalkeeper",
        goalkeeper_type=gk_type,
        location=location if location is not None else [5.0, 40.0],
    )


def gk_pass(match_id, period, minute, player, team, length, complete):
    return _blank(
        type="Pass",
        match_id=match_id,
        period=period,
        minute=minute,
        player=player,
        team=team,
        position="Goalkeeper",
        location=[10.0, 40.0],
        pass_outcome=None if complete else "Incomplete",
        pass_length=length,
        pass_end_location=[10.0 + length, 40.0],
        pass_height="Ground Pass",
        pass_body_part="Right Foot",
    )


def filler(match_id, period, minute, team="Team X"):
    """
    Evento de jogador de campo que fixa o período final do jogo.

    A duração regulamentar deriva do último período presente, não do minuto
    máximo — por isso é o `period` deste evento que determina 90 ou 120.
    """
    return _blank(
        type="Pass",
        match_id=match_id,
        period=period,
        minute=minute,
        player="Outfield Player",
        team=team,
        position="Center Back",
        location=[50.0, 40.0],
        pass_length=15.0,
        pass_end_location=[65.0, 40.0],
        pass_height="Ground Pass",
        pass_body_part="Right Foot",
    )


def build_synthetic_events() -> pd.DataFrame:
    rows = []

    # ------------------------- Jogo 1 (90') -------------------------
    rows.append(starting_xi(1, "Team X", [("Keeper A", "Goalkeeper"),
                                          ("Outfield Player", "Center Back")]))
    rows.append(starting_xi(1, "Team Y", [("Keeper B", "Goalkeeper")]))

    for _ in range(3):
        rows.append(gk_event(1, 1, 10, "Keeper A", "Team X", "Shot Saved"))
    rows.append(gk_event(1, 1, 20, "Keeper A", "Team X", "Goal Conceded"))
    for _ in range(2):
        rows.append(gk_event(1, 1, 30, "Keeper A", "Team X", "Shot Faced"))
    for location, _distance in SWEEPER_LOCATIONS:
        rows.append(gk_event(1, 1, 40, "Keeper A", "Team X", "Keeper Sweeper", location))

    rows.append(gk_event(1, 1, 15, "Keeper B", "Team Y", "Shot Saved"))
    rows.append(gk_event(1, 1, 25, "Keeper B", "Team Y", "Goal Conceded"))
    rows.append(gk_event(1, 1, 35, "Keeper B", "Team Y", "Shot Faced"))

    # Keeper A: 5 passes -> 3 completos, comprimentos 20/30/50/60/40
    for length, complete in [(20.0, True), (30.0, True), (50.0, False),
                             (60.0, False), (40.0, True)]:
        rows.append(gk_pass(1, 2, 50, "Keeper A", "Team X", length, complete))

    for length in (10.0, 30.0):
        rows.append(gk_pass(1, 2, 55, "Keeper B", "Team Y", length, True))

    rows.append(filler(1, 2, 90))

    # ------------------- Jogo 2 (120', prolongamento) -------------------
    rows.append(starting_xi(2, "Team X", [("Keeper A", "Goalkeeper")]))
    rows.append(gk_event(2, 1, 10, "Keeper A", "Team X", "Shot Saved"))
    for _ in range(2):
        rows.append(gk_event(2, 1, 20, "Keeper A", "Team X", "Shot Faced"))
    rows.append(filler(2, 4, 120))

    # --------------- Jogo 3 (90', substituição de guarda-redes) ---------------
    rows.append(starting_xi(3, "Team Z", [("Keeper C", "Goalkeeper")]))

    for _ in range(2):
        rows.append(gk_event(3, 1, 10, "Keeper C", "Team Z", "Shot Saved"))
    rows.append(gk_pass(3, 1, 20, "Keeper C", "Team Z", 45.0, True))

    rows.append(substitution(3, 2, 60, "Team Z", "Keeper C", "Keeper D"))

    rows.append(gk_event(3, 2, 85, "Keeper D", "Team Z", "Shot Faced"))
    rows.append(filler(3, 2, 90, team="Team Z"))

    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


@pytest.fixture
def synthetic_events():
    return build_synthetic_events()


@pytest.fixture
def synthetic_table(synthetic_events):
    """Tabela de scouting completa construída a partir do dataset sintético."""
    return build_scouting_table(
        synthetic_events,
        build_gk_events(synthetic_events),
        build_gk_passes(synthetic_events),
    )
