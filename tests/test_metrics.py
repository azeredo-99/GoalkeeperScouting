"""
Testes para as métricas de shot stopping.

Cobrem a correção do denominador da percentagem de defesas (M1):
`Shot Faced` e `Shot Saved` são categorias disjuntas de `goalkeeper_type`,
por isso o denominador correto é `defesas + golos sofridos`, e não
`Shot Faced`.
"""

import numpy as np
import pandas as pd
import pytest

from gk_scouting.metrics import shot_stopping_metrics


PLAYER = "Test Keeper"


def make_gk_events(counts: dict[str, int], player: str = PLAYER) -> pd.DataFrame:
    """Constrói eventos de guarda-redes a partir de {goalkeeper_type: n}."""
    rows = [
        {"player": player, "goalkeeper_type": gk_type}
        for gk_type, n in counts.items()
        for _ in range(n)
    ]
    return pd.DataFrame(rows, columns=["player", "goalkeeper_type"])


def save_pct_of(counts: dict[str, int]) -> float:
    return shot_stopping_metrics(make_gk_events(counts)).loc[PLAYER, "save_pct"]


# ---------------------------------------------------------------------------
# Casos pedidos explicitamente
# ---------------------------------------------------------------------------

def test_ten_saves_five_goals_is_two_thirds():
    assert save_pct_of({"Shot Saved": 10, "Goal Conceded": 5}) == pytest.approx(66.666667)


def test_no_saves_is_zero_percent():
    assert save_pct_of({"Shot Saved": 0, "Goal Conceded": 5}) == 0.0


def test_no_goals_conceded_is_one_hundred_percent():
    assert save_pct_of({"Shot Saved": 10, "Goal Conceded": 0}) == 100.0


def test_no_shots_on_target_is_nan_not_zero_and_not_hundred():
    """
    Comportamento explicitamente definido: sem remates enquadrados a
    percentagem é indefinida (NaN). Tratá-la como 0% penalizaria o
    guarda-redes e tratá-la como 100% premiá-lo-ia, ambos sem base.
    """
    result = save_pct_of({"Shot Faced": 7})
    assert np.isnan(result)


# ---------------------------------------------------------------------------
# Estrutura real de goalkeeper_type
# ---------------------------------------------------------------------------

def test_shot_faced_is_excluded_from_denominator():
    """
    O bug original: `Shot Faced` são remates que nunca exigiram defesa
    (Off T / Blocked / Post / Wayward). Acrescentá-los não pode alterar
    a percentagem de defesas.
    """
    without = save_pct_of({"Shot Saved": 10, "Goal Conceded": 5})
    with_faced = save_pct_of({"Shot Saved": 10, "Goal Conceded": 5, "Shot Faced": 40})
    assert without == with_faced == pytest.approx(66.666667)


def test_old_formula_would_have_given_a_different_answer():
    """Teste de regressão explícito contra a fórmula antiga saves/faced."""
    counts = {"Shot Saved": 10, "Goal Conceded": 5, "Shot Faced": 40}
    old_formula = 10 / 40 * 100  # 25.0
    assert save_pct_of(counts) == pytest.approx(66.666667)
    assert save_pct_of(counts) != pytest.approx(old_formula)


def test_shot_saved_to_post_counts_as_a_save():
    """Remate enquadrado defendido para o poste é uma defesa."""
    result = shot_stopping_metrics(
        make_gk_events({"Shot Saved": 9, "Shot Saved to Post": 1, "Goal Conceded": 5})
    )
    assert result.loc[PLAYER, "shots_saved"] == 10
    assert result.loc[PLAYER, "save_pct"] == pytest.approx(66.666667)


def test_shot_saved_off_target_is_ignored():
    """O remate ia para fora: não era enquadrado, não entra na percentagem."""
    baseline = save_pct_of({"Shot Saved": 10, "Goal Conceded": 5})
    with_off_target = save_pct_of(
        {"Shot Saved": 10, "Goal Conceded": 5, "Shot Saved Off Target": 3}
    )
    assert baseline == with_off_target


def test_penalties_are_excluded():
    """
    A maioria dos eventos de penálti pertence a desempates, que por
    convenção não contam para a percentagem de defesas.
    """
    baseline = save_pct_of({"Shot Saved": 10, "Goal Conceded": 5})
    with_penalties = save_pct_of(
        {
            "Shot Saved": 10,
            "Goal Conceded": 5,
            "Penalty Saved": 4,
            "Penalty Conceded": 6,
        }
    )
    assert baseline == with_penalties


def test_non_shot_actions_do_not_affect_save_pct():
    """Recolhas, socos e saídas não são defesas a remate."""
    baseline = save_pct_of({"Shot Saved": 10, "Goal Conceded": 5})
    with_actions = save_pct_of(
        {
            "Shot Saved": 10,
            "Goal Conceded": 5,
            "Collected": 12,
            "Punch": 7,
            "Keeper Sweeper": 5,
            "Smother": 2,
        }
    )
    assert baseline == with_actions


# ---------------------------------------------------------------------------
# shots_faced e invariantes
# ---------------------------------------------------------------------------

def test_shots_faced_counts_every_shot_faced():
    """`shots_faced` = enquadrados (defendidos + sofridos) + não enquadrados."""
    result = shot_stopping_metrics(
        make_gk_events({"Shot Saved": 10, "Goal Conceded": 5, "Shot Faced": 40})
    )
    row = result.loc[PLAYER]
    assert row["shots_faced"] == 55
    assert row["shots_saved"] == 10
    assert row["goals_conceded"] == 5


def test_multiple_keepers_are_aggregated_independently():
    events = pd.concat(
        [
            make_gk_events({"Shot Saved": 8, "Goal Conceded": 2}, player="Keeper A"),
            make_gk_events({"Shot Saved": 3, "Goal Conceded": 7}, player="Keeper B"),
        ],
        ignore_index=True,
    )
    result = shot_stopping_metrics(events)
    assert result.loc["Keeper A", "save_pct"] == pytest.approx(80.0)
    assert result.loc["Keeper B", "save_pct"] == pytest.approx(30.0)


def test_save_pct_always_within_bounds():
    for saves, goals in [(0, 1), (1, 0), (7, 3), (1, 99), (99, 1)]:
        value = save_pct_of({"Shot Saved": saves, "Goal Conceded": goals})
        assert 0.0 <= value <= 100.0


def test_empty_input_returns_expected_columns():
    result = shot_stopping_metrics(pd.DataFrame())
    assert list(result.columns) == [
        "shots_faced",
        "shots_saved",
        "goals_conceded",
        "save_pct",
    ]
    assert result.empty
