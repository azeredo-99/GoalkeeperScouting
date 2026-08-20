"""
Testes para os defaults e os pesos do motor de similaridade (P0-6).

Cobrem duas correções:

* o limiar de minutos deixa de ser um valor fixo (720) e passa a derivar
  da distribuição real da amostra;
* os pesos passam a ser expostos como proporção efetiva, e o comportamento
  para pesos inválidos passa a ser explícito.
"""

import pandas as pd
import pytest

from gk_scouting.similarity_engine import (
    DEFAULT_DIMENSION_WEIGHTS,
    MIN_MINUTES_FLOOR,
    default_min_minutes,
    find_similar_goalkeepers,
    normalise_dimension_weights,
)


# ---------------------------------------------------------------------------
# default_min_minutes
# ---------------------------------------------------------------------------

def test_default_is_p25_floored_to_whole_matches():
    # P25 = 286 -> arredondado para baixo = 270 (três jogos completos).
    minutes = pd.Series([180, 286, 300, 400, 739])
    assert minutes.quantile(0.25) == 286
    assert default_min_minutes(minutes) == 270


def test_default_is_a_multiple_of_a_full_match():
    for sample in ([190, 200, 300, 800], [180, 500, 1200, 3371], [95, 100, 120, 130]):
        assert default_min_minutes(pd.Series(sample)) % 90 == 0


def test_default_keeps_at_least_three_quarters_of_the_sample():
    """
    É esta a propriedade que interessa: o default tem de deixar candidatos
    na primeira utilização. O valor antigo (720) deixava 2 de 41.
    """
    minutes = pd.Series([180, 202, 250, 286, 300, 350, 389, 450, 600, 739])
    threshold = default_min_minutes(minutes)
    eligible = (minutes >= threshold).sum()
    assert eligible >= 0.75 * len(minutes)


def test_old_hardcoded_default_would_have_excluded_almost_everyone():
    """Regressão explícita contra o valor fixo anterior."""
    minutes = pd.Series([180, 202, 250, 286, 300, 350, 389, 450, 600, 739])
    assert (minutes >= 720).sum() == 1
    assert (minutes >= default_min_minutes(minutes)).sum() >= 8


def test_default_never_below_the_floor():
    assert default_min_minutes(pd.Series([90, 91, 92])) == MIN_MINUTES_FLOOR


def test_default_handles_empty_and_invalid_input():
    assert default_min_minutes(pd.Series([], dtype=float)) == MIN_MINUTES_FLOOR
    assert default_min_minutes([]) == MIN_MINUTES_FLOOR
    assert default_min_minutes(pd.Series([None, None])) == MIN_MINUTES_FLOOR


def test_default_ignores_non_numeric_values():
    assert default_min_minutes(pd.Series([180, 286, 300, 400, 739])) == 270
    assert default_min_minutes(pd.Series([180, "n/a", 286, 300, 400, 739])) == 270


# ---------------------------------------------------------------------------
# normalise_dimension_weights
# ---------------------------------------------------------------------------

def test_weights_sum_to_one():
    result = normalise_dimension_weights({"Shot Stopping": 30, "Distribution": 35, "Proactivity": 35})
    assert sum(result.values()) == pytest.approx(1.0)


def test_equal_weights_produce_equal_dimensions():
    result = normalise_dimension_weights({"Shot Stopping": 10, "Distribution": 10, "Proactivity": 10})
    assert all(v == pytest.approx(1 / 3) for v in result.values())


def test_only_the_proportion_matters_not_the_absolute_value():
    """
    30/35/35 e 60/70/70 são o mesmo perfil. Isto é o comportamento correto
    — o problema era a interface sugerir que a soma tinha de dar 100.
    """
    a = normalise_dimension_weights({"Shot Stopping": 30, "Distribution": 35, "Proactivity": 35})
    b = normalise_dimension_weights({"Shot Stopping": 60, "Distribution": 70, "Proactivity": 70})
    assert a == pytest.approx(b)


def test_different_proportions_produce_different_weights():
    a = normalise_dimension_weights({"Shot Stopping": 30, "Distribution": 35, "Proactivity": 35})
    b = normalise_dimension_weights({"Shot Stopping": 60, "Distribution": 20, "Proactivity": 20})
    assert a != pytest.approx(b)
    assert b["Shot Stopping"] == pytest.approx(0.6)


def test_zero_weight_dimension_is_dropped_from_the_profile():
    result = normalise_dimension_weights({"Shot Stopping": 0, "Distribution": 50, "Proactivity": 50})
    assert result["Shot Stopping"] == 0.0
    assert result["Distribution"] == pytest.approx(0.5)


def test_negative_weights_are_rejected():
    with pytest.raises(ValueError, match="negativo"):
        normalise_dimension_weights({"Shot Stopping": -10, "Distribution": 50, "Proactivity": 50})


def test_all_zero_weights_raise_explicitly():
    """Comportamento explicitamente definido: sem dimensões não há perfil."""
    with pytest.raises(ValueError, match="superior a 0"):
        normalise_dimension_weights({"Shot Stopping": 0, "Distribution": 0, "Proactivity": 0})


def test_defaults_are_used_when_nothing_is_passed():
    assert normalise_dimension_weights() == pytest.approx(
        normalise_dimension_weights(DEFAULT_DIMENSION_WEIGHTS)
    )


def test_missing_dimension_is_treated_as_zero():
    result = normalise_dimension_weights({"Distribution": 50, "Proactivity": 50})
    assert result["Shot Stopping"] == 0.0


# ---------------------------------------------------------------------------
# Os pesos alteram efetivamente os resultados
# ---------------------------------------------------------------------------

def weighted_table():
    """
    'Shot Twin' tem a mesma eficácia de defesas do alvo mas distribuição
    diferente. 'Pass Twin' é o inverso. O perfil escolhido deve decidir
    qual dos dois fica em primeiro.
    """
    return pd.DataFrame(
        {
            "minutes": [900, 900, 900, 900, 900],
            "save_pct": [70.0, 70.0, 40.0, 55.0, 85.0],
            "pass_success_pct": [85.0, 60.0, 85.0, 72.0, 55.0],
            "avg_pass_length": [30.0, 50.0, 30.0, 40.0, 55.0],
            "long_ball_pct": [25.0, 60.0, 25.0, 42.0, 70.0],
            "sweeper_actions_p90": [2.0, 2.0, 2.0, 3.5, 1.0],
            "avg_distance_from_goal": [15.0, 15.0, 15.0, 22.0, 11.0],
        },
        index=["Target", "Shot Twin", "Pass Twin", "Filler A", "Filler B"],
    )


def test_weighting_shot_stopping_ranks_the_shot_stopping_twin_first():
    result = find_similar_goalkeepers(
        weighted_table(),
        "Target",
        top_n=4,
        min_minutes=180,
        dimension_weights={"Shot Stopping": 100, "Distribution": 0, "Proactivity": 0},
    )
    assert result.index[0] == "Shot Twin"


def test_weighting_distribution_ranks_the_distribution_twin_first():
    result = find_similar_goalkeepers(
        weighted_table(),
        "Target",
        top_n=4,
        min_minutes=180,
        dimension_weights={"Shot Stopping": 0, "Distribution": 100, "Proactivity": 0},
    )
    assert result.index[0] == "Pass Twin"


def test_changing_weights_changes_the_scores():
    shot = find_similar_goalkeepers(
        weighted_table(), "Target", top_n=4, min_minutes=180,
        dimension_weights={"Shot Stopping": 100, "Distribution": 0, "Proactivity": 0},
    )
    balanced = find_similar_goalkeepers(
        weighted_table(), "Target", top_n=4, min_minutes=180,
        dimension_weights={"Shot Stopping": 34, "Distribution": 33, "Proactivity": 33},
    )
    assert shot.loc["Shot Twin", "similarity_pct"] != pytest.approx(
        balanced.loc["Shot Twin", "similarity_pct"]
    )


# ---------------------------------------------------------------------------
# Candidatos: com e sem
# ---------------------------------------------------------------------------

def test_returns_candidates_with_a_valid_target():
    result = find_similar_goalkeepers(weighted_table(), "Target", top_n=3, min_minutes=180)
    assert len(result) == 3
    assert "Target" not in result.index
    assert result["similarity_pct"].is_monotonic_decreasing


def test_no_candidates_when_threshold_excludes_everyone_but_the_target():
    table = weighted_table()
    table.loc["Target", "minutes"] = 900
    table.loc[table.index != "Target", "minutes"] = 100
    result = find_similar_goalkeepers(table, "Target", top_n=5, min_minutes=180)
    assert result.empty


def test_target_below_threshold_raises_a_clear_error():
    table = weighted_table()
    table.loc["Target", "minutes"] = 100
    with pytest.raises(ValueError, match="180"):
        find_similar_goalkeepers(table, "Target", top_n=5, min_minutes=180)


def test_unknown_target_raises():
    with pytest.raises(ValueError, match="não existe"):
        find_similar_goalkeepers(weighted_table(), "Nobody", top_n=5, min_minutes=180)


def test_empty_table_returns_empty_frame():
    assert find_similar_goalkeepers(pd.DataFrame(), "Target").empty
