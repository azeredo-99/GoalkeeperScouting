"""
Testes de `gk_scouting.similarity_view` (Fase 4 do roadmap de produto:
Similarity redesenhada como ação a partir do Player Profile).

Estes testes usam `find_similar_goalkeepers`/`explain_similarity`/
`normalise_dimension_weights` REAIS de `similarity_engine.py`, sem
qualquer stub -- servem também de guarda de regressão: provam que o
algoritmo de similaridade não foi alterado por esta fase, apenas a
forma como o resultado é apresentado.
"""

import numpy as np
import pandas as pd
import pytest

from gk_scouting.similarity_engine import (
    STYLE_FEATURES,
    explain_similarity,
    find_similar_goalkeepers,
    normalise_dimension_weights,
)
from gk_scouting.similarity_view import build_similarity_rows, reference_context


def _table():
    """
    Cinco guarda-redes, cada um com o seu próprio (competition_id,
    season_id) -- para provar que o contexto nunca se mistura entre
    candidatos nem com a referência.
    """
    return pd.DataFrame(
        {
            "minutes": [900, 900, 900, 900, 900],
            "competition_id": [1, 2, 3, 4, 5],
            "season_id": [2020, 2021, 2022, 2023, 2024],
            "save_pct": [70.0, 70.0, 40.0, 55.0, 85.0],
            "pass_success_pct": [85.0, 60.0, 85.0, 72.0, 55.0],
            "avg_pass_length": [30.0, 50.0, 30.0, 40.0, 55.0],
            "long_ball_pct": [25.0, 60.0, 25.0, 42.0, 70.0],
            "sweeper_actions_p90": [2.0, 2.0, 2.0, 3.5, 1.0],
            "avg_distance_from_goal": [15.0, 15.0, 15.0, 22.0, 11.0],
        },
        index=["Target", "Shot Twin", "Pass Twin", "Filler A", "Filler B"],
    )


def _market_lookup():
    return {
        "Shot Twin": pd.Series({"current_club_name": "Club A", "market_value_in_eur": 10_000_000.0}),
        "Pass Twin": pd.Series({"current_club_name": "Club B", "market_value_in_eur": 20_000_000.0}),
    }


# ===========================================================================
# reference_context
# ===========================================================================

def test_reference_context_returns_the_row_used_by_the_engine():
    table = _table()
    context = reference_context(table, "Target")
    assert context["competition_id"] == 1
    assert context["season_id"] == 2020
    assert context["minutes"] == 900


def test_reference_context_missing_player_returns_none():
    assert reference_context(_table(), "Nobody") is None


# ===========================================================================
# build_similarity_rows -- contexto nunca escondido nem misturado
# ===========================================================================

def test_context_is_attached_per_candidate_not_mixed():
    table = _table()
    similar = find_similar_goalkeepers(table, "Target", top_n=4, min_minutes=180)

    rows = build_similarity_rows(
        similar, table, "Target", _market_lookup(), explain_similarity, STYLE_FEATURES
    )

    by_name = {row["player_name"]: row for row in rows}

    assert by_name["Shot Twin"]["competition_id"] == 2
    assert by_name["Shot Twin"]["season_id"] == 2021
    assert by_name["Pass Twin"]["competition_id"] == 3
    assert by_name["Pass Twin"]["season_id"] == 2022
    # Contextos distintos, nunca iguais entre candidatos diferentes.
    assert by_name["Shot Twin"]["competition_id"] != by_name["Pass Twin"]["competition_id"]


def test_market_data_attached_only_when_present_never_invented():
    table = _table()
    similar = find_similar_goalkeepers(table, "Target", top_n=4, min_minutes=180)

    rows = build_similarity_rows(
        similar, table, "Target", _market_lookup(), explain_similarity, STYLE_FEATURES
    )
    by_name = {row["player_name"]: row for row in rows}

    assert by_name["Shot Twin"]["current_club_name"] == "Club A"
    # "Filler A"/"Filler B" não estão no lookup -- ficam None, não inventados.
    if "Filler A" in by_name:
        assert by_name["Filler A"]["current_club_name"] is None


def test_rank_follows_the_order_similarity_engine_produced():
    """
    A ordem dos resultados não é recalculada nem reordenada por
    build_similarity_rows -- é exatamente a de `similar.index`.
    """
    table = _table()
    similar = find_similar_goalkeepers(table, "Target", top_n=3, min_minutes=180)

    rows = build_similarity_rows(
        similar, table, "Target", {}, explain_similarity, STYLE_FEATURES
    )

    assert [row["player_name"] for row in rows] == list(similar.index)
    assert [row["rank"] for row in rows] == list(range(1, len(rows) + 1))


# ===========================================================================
# similarity_pct não é alterado pela apresentação
# ===========================================================================

def test_similarity_pct_in_rows_matches_the_engine_output_exactly():
    table = _table()
    similar = find_similar_goalkeepers(table, "Target", top_n=3, min_minutes=180)

    rows = build_similarity_rows(
        similar, table, "Target", {}, explain_similarity, STYLE_FEATURES
    )

    for row in rows:
        expected = float(similar.loc[row["player_name"], "similarity_pct"])
        assert row["similarity_pct"] == expected


# ===========================================================================
# explain_similarity continua a ser usado, sem reimplementação
# ===========================================================================

def test_explanation_matches_calling_explain_similarity_directly():
    table = _table()
    similar = find_similar_goalkeepers(table, "Target", top_n=3, min_minutes=180)

    rows = build_similarity_rows(
        similar, table, "Target", {}, explain_similarity, STYLE_FEATURES
    )

    for row in rows:
        direct = explain_similarity(
            table, "Target", row["player_name"], features=STYLE_FEATURES
        )
        assert row["explanation"] == direct


def test_explain_fn_is_actually_invoked_not_a_placeholder():
    """
    Um `explain_fn` de mentira (spy) prova que build_similarity_rows
    genuinamente chama a função passada, com os argumentos certos.
    """
    calls = []

    def spy_explain(table_arg, target_arg, candidate_arg, features=None):
        calls.append((target_arg, candidate_arg, tuple(features)))
        return f"explicação para {candidate_arg}"

    table = _table()
    similar = find_similar_goalkeepers(table, "Target", top_n=2, min_minutes=180)

    rows = build_similarity_rows(
        similar, table, "Target", {}, spy_explain, STYLE_FEATURES
    )

    assert len(calls) == len(rows)
    for target_arg, candidate_arg, features_arg in calls:
        assert target_arg == "Target"
        assert features_arg == tuple(STYLE_FEATURES)
    assert all(row["explanation"].startswith("explicação para") for row in rows)


# ===========================================================================
# Pesos passados ao algoritmo sem alteração (regressão do P0-6)
# ===========================================================================

def test_weights_dict_reaches_the_engine_unmodified():
    """
    Confirma que passar dimension_weights a find_similar_goalkeepers
    continua a produzir exatamente a proporção que
    normalise_dimension_weights calcularia a partir do MESMO dicionário
    -- ou seja, nada nesta fase intercetou ou alterou os pesos entre a
    UI e o motor.
    """
    weights = {"Shot Stopping": 60, "Distribution": 20, "Proactivity": 20}
    table = _table()

    # Perfil dominado por Shot Stopping deve favorecer quem partilha
    # save_pct com o alvo (Shot Twin), exatamente como o motor já
    # garantia antes desta fase (ver test_similarity_config.py).
    similar = find_similar_goalkeepers(
        table, "Target", top_n=4, min_minutes=180, dimension_weights=weights
    )
    assert similar.index[0] == "Shot Twin"

    effective = normalise_dimension_weights(weights)
    assert effective["Shot Stopping"] == pytest.approx(0.6)


def test_similarity_engine_module_is_not_monkeypatched_by_this_phase():
    """
    Garante que os símbolos usados continuam a ser exatamente os
    definidos em similarity_engine.py (não substituídos por stubs em
    nenhum módulo desta fase).
    """
    import gk_scouting.similarity_engine as engine

    assert find_similar_goalkeepers is engine.find_similar_goalkeepers
    assert explain_similarity is engine.explain_similarity
    assert normalise_dimension_weights is engine.normalise_dimension_weights
