"""
Testes da dimensão competição/época (P0-5).

Cobrem o parâmetro opcional `context_columns` de `build_scouting_table()`:
sem ele, o comportamento tem de ser byte-a-byte idêntico ao anterior a
esta alteração (uma linha por jogador, contextos misturados). Com ele,
o mesmo jogador em competições/épocas diferentes passa a ter uma linha
por combinação, sem misturar valores.

Reutiliza os helpers de `conftest.py`, acrescentando `competition_id` e
`season_id` aos eventos onde o cenário precisa deles.
"""

import numpy as np
import pandas as pd
import pytest

from conftest import (
    EVENT_COLUMNS,
    filler,
    gk_event,
    gk_pass,
    starting_xi,
)
from gk_scouting.data_loader import build_gk_events, build_gk_passes
from gk_scouting.metrics import CONTEXT_COLUMNS, build_scouting_table


def with_context(row, competition_id, season_id, competition_name=None, player_id=None):
    """Acrescenta colunas de contexto (e opcionalmente player_id) a um evento."""
    row = dict(row)
    row["competition_id"] = competition_id
    row["season_id"] = season_id
    row["competition_name"] = competition_name
    row["player_id"] = player_id
    return row


CONTEXT_EVENT_COLUMNS = [
    *EVENT_COLUMNS,
    "competition_id",
    "season_id",
    "competition_name",
    "player_id",
]


def events_from(rows):
    return pd.DataFrame(rows, columns=CONTEXT_EVENT_COLUMNS)


def build_two_competition_events():
    """
    Um único guarda-redes, dois jogos em competições/épocas diferentes.

    Jogo 1 (Competição A, época 2022): 8 defesas, 2 golos sofridos.
    Jogo 2 (Competição B, época 2023): 2 defesas, 8 golos sofridos.

    Os totais são deliberadamente opostos para que qualquer mistura entre
    contextos produza um save% claramente diferente de ambos os valores
    corretos (80% e 20%) — o teste que os mistura falharia de forma óbvia.
    """
    rows = []

    rows.append(with_context(
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        competition_id=1, season_id=2022, competition_name="Competição A",
    ))
    for _ in range(8):
        rows.append(with_context(
            gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
            competition_id=1, season_id=2022, competition_name="Competição A",
        ))
    for _ in range(2):
        rows.append(with_context(
            gk_event(1, 1, 20, "Keeper", "Team X", "Goal Conceded"),
            competition_id=1, season_id=2022, competition_name="Competição A",
        ))
    rows.append(with_context(
        filler(1, 2, 90),
        competition_id=1, season_id=2022, competition_name="Competição A",
    ))

    rows.append(with_context(
        starting_xi(2, "Team X", [("Keeper", "Goalkeeper")]),
        competition_id=2, season_id=2023, competition_name="Competição B",
    ))
    for _ in range(2):
        rows.append(with_context(
            gk_event(2, 1, 10, "Keeper", "Team X", "Shot Saved"),
            competition_id=2, season_id=2023, competition_name="Competição B",
        ))
    for _ in range(8):
        rows.append(with_context(
            gk_event(2, 1, 20, "Keeper", "Team X", "Goal Conceded"),
            competition_id=2, season_id=2023, competition_name="Competição B",
        ))
    rows.append(with_context(
        filler(2, 2, 90),
        competition_id=2, season_id=2023, competition_name="Competição B",
    ))

    return events_from(rows)


def table_for(events, **kwargs):
    return build_scouting_table(
        events,
        build_gk_events(events),
        build_gk_passes(events),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Sem context_columns: comportamento intocado
# ---------------------------------------------------------------------------

def test_default_call_signature_still_produces_one_row_per_player():
    """
    Sem `context_columns`, o comportamento é o de sempre: uma linha por
    jogador, mesmo quando os eventos têm colunas de competição/época.
    """
    events = build_two_competition_events()
    table = table_for(events)

    assert list(table.index) == ["Keeper"]
    assert isinstance(table.index, pd.Index)
    assert not isinstance(table.index, pd.MultiIndex)


def test_default_call_mixes_contexts_exactly_like_before():
    """
    Este é o comportamento histórico (o problema que o P0-5 existe para
    resolver quando pedido explicitamente) — continua a acontecer por
    omissão, de propósito, para não alterar a aplicação existente.

        10 defesas totais / (10 defesas + 10 golos) = 50%

    Nem 80% (competição A) nem 20% (competição B): a prova de que os
    contextos foram somados antes de calcular a percentagem.
    """
    events = build_two_competition_events()
    table = table_for(events)

    assert table.loc["Keeper", "shots_saved"] == 10
    assert table.loc["Keeper", "goals_conceded"] == 10
    assert table.loc["Keeper", "save_pct"] == pytest.approx(50.0)
    assert table.loc["Keeper", "minutes"] == 180.0


def test_context_columns_absent_falls_back_silently():
    """
    Pedir separação por contexto num dataset sem essas colunas (como
    `events_full_wc2022.pkl`) não é erro — degrada-se para o mesmo
    resultado do caminho por omissão, com o mesmo tipo de índice.
    """
    events = pd.DataFrame(
        [
            starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
            gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
            filler(1, 2, 90),
        ],
        columns=EVENT_COLUMNS,
    )
    default = table_for(events)
    requested = table_for(events, context_columns=CONTEXT_COLUMNS)

    assert not isinstance(requested.index, pd.MultiIndex)
    pd.testing.assert_frame_equal(default, requested)


# ---------------------------------------------------------------------------
# Com context_columns: uma linha por (player, competition_id, season_id)
# ---------------------------------------------------------------------------

def test_same_player_in_two_competitions_produces_two_rows():
    events = build_two_competition_events()
    table = table_for(events, context_columns=CONTEXT_COLUMNS)

    assert isinstance(table.index, pd.MultiIndex)
    assert table.index.names == ["player", "competition_id", "season_id"]
    assert len(table) == 2
    assert set(table.index) == {("Keeper", 1, 2022), ("Keeper", 2, 2023)}


def test_context_values_are_not_mixed():
    """
    A propriedade central desta fase: cada linha reflete só o jogo da sua
    competição/época, com os valores exatos calculados à mão.
    """
    events = build_two_competition_events()
    table = table_for(events, context_columns=CONTEXT_COLUMNS)

    row_a = table.loc[("Keeper", 1, 2022)]
    assert row_a["shots_saved"] == 8
    assert row_a["goals_conceded"] == 2
    assert row_a["save_pct"] == pytest.approx(80.0)
    assert row_a["minutes"] == 90.0

    row_b = table.loc[("Keeper", 2, 2023)]
    assert row_b["shots_saved"] == 2
    assert row_b["goals_conceded"] == 8
    assert row_b["save_pct"] == pytest.approx(20.0)
    assert row_b["minutes"] == 90.0


def test_context_rows_sum_back_to_the_mixed_default():
    """
    Verificação cruzada: a soma das duas linhas contextuais bate certo com
    o total agregado sem contexto -- prova que nenhum evento se perdeu nem
    foi duplicado ao fatiar por match_id.
    """
    events = build_two_competition_events()
    default = table_for(events)
    contextual = table_for(events, context_columns=CONTEXT_COLUMNS)

    assert contextual["shots_saved"].sum() == default.loc["Keeper", "shots_saved"]
    assert contextual["goals_conceded"].sum() == default.loc["Keeper", "goals_conceded"]
    assert contextual["minutes"].sum() == default.loc["Keeper", "minutes"]


def test_partial_context_degrades_to_the_available_column():
    """
    Se só `competition_id` estiver presente (sem `season_id`), a separação
    usa apenas o que existe -- não falha nem inventa a coluna em falta.
    """
    events = build_two_competition_events().drop(columns=["season_id"])
    table = table_for(events, context_columns=CONTEXT_COLUMNS)

    assert table.index.names == ["player", "competition_id"]
    assert len(table) == 2


def test_single_competition_dataset_produces_a_single_context_row():
    """Um dataset com uma só competição/época dá uma linha, não duas."""
    events = pd.DataFrame(
        [
            with_context(
                starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
                competition_id=9, season_id=2022,
            ),
            with_context(
                gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
                competition_id=9, season_id=2022,
            ),
            with_context(filler(1, 2, 90), competition_id=9, season_id=2022),
        ],
        columns=CONTEXT_EVENT_COLUMNS,
    )
    table = table_for(events, context_columns=CONTEXT_COLUMNS)

    assert len(table) == 1
    assert table.index[0] == ("Keeper", 9, 2022)


def test_empty_events_with_context_columns_returns_empty_multiindex():
    events = events_from([])
    table = table_for(events, context_columns=CONTEXT_COLUMNS)

    assert table.empty
    assert isinstance(table.index, pd.MultiIndex)
    assert table.index.names == ["player", "competition_id", "season_id"]


# ---------------------------------------------------------------------------
# player_id preservado pelo data_loader
# ---------------------------------------------------------------------------

def test_player_id_is_preserved_when_present():
    events = pd.DataFrame(
        [
            with_context(
                starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
                competition_id=1, season_id=2022,
            ),
            with_context(
                gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
                competition_id=1, season_id=2022, player_id=555,
            ),
            with_context(filler(1, 2, 90), competition_id=1, season_id=2022),
        ],
        columns=CONTEXT_EVENT_COLUMNS,
    )
    gk_events = build_gk_events(events)

    assert "player_id" in gk_events.columns
    assert gk_events.loc[gk_events["player"] == "Keeper", "player_id"].iloc[0] == 555


def test_player_id_absent_is_handled_gracefully():
    """
    Sem `player_id` nos eventos (dataset de competição única mais antigo),
    a coluna simplesmente não aparece -- sem erro, sem coluna de NaN.
    """
    events = pd.DataFrame(
        [
            starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
            gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
            filler(1, 2, 90),
        ],
        columns=EVENT_COLUMNS,
    )
    gk_events = build_gk_events(events)
    gk_passes = build_gk_passes(events)

    assert "player_id" not in gk_events.columns
    assert "player_id" not in gk_passes.columns


def test_context_columns_preserved_on_gk_events_and_gk_passes():
    """
    Preparação para consumo direto por uma futura API: as colunas de
    contexto não dependem de passar por build_scouting_table.
    """
    events = build_two_competition_events()
    gk_events = build_gk_events(events)
    gk_passes = build_gk_passes(events)

    assert {"competition_id", "season_id", "competition_name"}.issubset(gk_events.columns)
    row = gk_events[gk_events["player"] == "Keeper"].iloc[0]
    assert row["competition_id"] in (1, 2)

    if not gk_passes.empty:
        assert {"competition_id", "season_id"}.issubset(gk_passes.columns)


# ---------------------------------------------------------------------------
# Validação contra o dataset real (Bounou)
# ---------------------------------------------------------------------------

import os  # noqa: E402

DATASET = os.path.join("data", "events_extended.pkl")


def dataset_available(path=DATASET) -> bool:
    """Mesmo guard de test_minutes.py: distingue pickle real de ponteiro LFS."""
    if not os.path.exists(path):
        return False
    with open(path, "rb") as handle:
        return handle.read(1) == b"\x80"


@pytest.mark.skipif(
    not dataset_available(),
    reason="events_extended.pkl não disponível (ausente ou ponteiro Git LFS)",
)
def test_real_dataset_splits_a_multi_competition_keeper():
    """
    Yassine Bounou apareceu, na investigação desta fase, agregado numa
    única linha somando AFCON 2023 + La Liga 2020/21 + World Cup 2022.
    Com `context_columns`, tem de aparecer em linhas separadas, uma por
    competição/época, e a soma dos minutos de cada linha não pode exceder
    os minutos de um único jogo daquela competição multiplicados pelo
    número de jogos que lá jogou.
    """
    events = pd.read_pickle(DATASET)
    gk_events = build_gk_events(events)
    gk_passes = build_gk_passes(events)

    default = build_scouting_table(events, gk_events, gk_passes)
    assert "Yassine Bounou" in default.index

    contextual = build_scouting_table(
        events, gk_events, gk_passes, context_columns=CONTEXT_COLUMNS
    )

    bounou_rows = contextual.loc[
        contextual.index.get_level_values("player") == "Yassine Bounou"
    ]

    assert len(bounou_rows) >= 3

    competitions = set(bounou_rows.index.get_level_values("competition_id"))
    assert len(competitions) >= 3

    # A soma das linhas contextuais tem de bater certo com o agregado
    # antigo -- garante que separar por contexto não perde nem duplica
    # minutos face ao comportamento por omissão.
    assert bounou_rows["minutes"].sum() == pytest.approx(
        default.loc["Yassine Bounou", "minutes"]
    )
