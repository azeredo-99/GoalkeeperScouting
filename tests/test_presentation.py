"""
Testes dos helpers de apresentação do Player Profile (Fase 2 do roadmap
de produto).

Cobrem só a lógica nova desta fase: formatação NaN-segura e seleção das
linhas de contexto de um jogador. Não testam HTML/CSS nem Streamlit --
`presentation.py` existe precisamente para separar essa lógica pura do
código com efeitos secundários em `streamlit_app.py`.
"""

import numpy as np
import pandas as pd
import pytest

from gk_scouting.presentation import (
    NO_ACTIONS_LABEL,
    context_label,
    format_count,
    format_distance_m,
    format_metric,
    format_percentage,
    format_rate_p90,
    player_context_rows,
)


# ---------------------------------------------------------------------------
# format_metric e wrappers -- NaN nunca vira "0"
# ---------------------------------------------------------------------------

def test_format_metric_formats_a_present_value():
    assert format_metric(73.456, "{:.1f}", "%") == "73.5%"


def test_format_metric_nan_is_not_zero():
    """O caso central pedido: NaN não pode aparecer como '0.0'."""
    result = format_metric(float("nan"), "{:.1f}", "%")
    assert result != "0.0%"
    assert result == "N/A"


def test_format_metric_none_uses_the_empty_label():
    assert format_metric(None) == "N/A"


def test_format_metric_numpy_nan_is_treated_as_missing():
    assert format_metric(np.nan, "{:.2f}") == "N/A"


def test_format_metric_custom_empty_label():
    result = format_metric(float("nan"), empty=NO_ACTIONS_LABEL)
    assert result == NO_ACTIONS_LABEL
    assert result != "0"


def test_format_metric_zero_is_not_confused_with_missing():
    """Um valor real de 0.0 tem de aparecer como 0, não como 'N/A'."""
    assert format_metric(0.0, "{:.1f}", "%") == "0.0%"


@pytest.mark.parametrize(
    "formatter, value, expected",
    [
        (format_percentage, 66.666667, "66.7%"),
        (format_count, 42.0, "42"),
        (format_rate_p90, 1.234, "1.23"),
        (format_distance_m, 17.71575, "17.7 m"),
    ],
)
def test_formatter_wrappers_produce_expected_output(formatter, value, expected):
    assert formatter(value) == expected


@pytest.mark.parametrize("formatter", [format_percentage, format_count, format_rate_p90, format_distance_m])
def test_all_formatter_wrappers_treat_nan_as_missing_not_zero(formatter):
    result = formatter(float("nan"))
    assert result == "N/A"
    assert "0" not in result


def test_sweeper_specific_empty_label_is_used_end_to_end():
    """
    Reproduz exatamente o caso real: um guarda-redes sem ações de
    sweeper tem sweeper_actions = NaN (ver metrics.py / M5-S3).
    """
    value = format_count(float("nan"), empty=NO_ACTIONS_LABEL)
    assert value == NO_ACTIONS_LABEL
    assert value != "0"


# ---------------------------------------------------------------------------
# context_label
# ---------------------------------------------------------------------------

def test_context_label_includes_ids_and_minutes():
    row = pd.Series({"competition_id": 43, "season_id": 106, "minutes": 690.0})
    label = context_label(row)
    assert "#43" in label
    assert "#106" in label
    assert "690" in label


# ---------------------------------------------------------------------------
# player_context_rows -- base do seletor de contexto
# ---------------------------------------------------------------------------

def _performances():
    return pd.DataFrame(
        [
            {"player_name": "Keeper A", "competition_id": 1, "season_id": 2022, "minutes": 300.0},
            {"player_name": "Keeper A", "competition_id": 2, "season_id": 2023, "minutes": 900.0},
            {"player_name": "Keeper B", "competition_id": 1, "season_id": 2022, "minutes": 500.0},
        ]
    )


def test_single_row_player_returns_one_row():
    rows = player_context_rows(_performances(), "Keeper B")
    assert len(rows) == 1
    assert rows.iloc[0]["competition_id"] == 1


def test_multi_context_player_returns_every_row_not_aggregated():
    """
    O requisito central: um jogador com várias linhas devolve TODAS,
    sem somar nem colapsar nenhuma métrica entre contextos.
    """
    rows = player_context_rows(_performances(), "Keeper A")
    assert len(rows) == 2
    assert set(rows["competition_id"]) == {1, 2}
    assert set(rows["minutes"]) == {300.0, 900.0}


def test_rows_are_ordered_by_minutes_descending():
    rows = player_context_rows(_performances(), "Keeper A")
    assert rows.iloc[0]["minutes"] == 900.0
    assert rows.iloc[1]["minutes"] == 300.0


def test_selecting_a_different_context_changes_every_metric_column():
    """
    Simula a troca de seletor: cada linha tem de trazer os SEUS próprios
    valores, nunca os de outro contexto.
    """
    performances = pd.DataFrame(
        [
            {"player_name": "Keeper A", "competition_id": 1, "season_id": 2022,
             "minutes": 300.0, "save_pct": 80.0, "shots_faced": 10.0},
            {"player_name": "Keeper A", "competition_id": 2, "season_id": 2023,
             "minutes": 900.0, "save_pct": 55.0, "shots_faced": 40.0},
        ]
    )
    rows = player_context_rows(performances, "Keeper A")

    row_2022 = rows[rows["competition_id"] == 1].iloc[0]
    row_2023 = rows[rows["competition_id"] == 2].iloc[0]

    assert row_2022["save_pct"] == 80.0
    assert row_2023["save_pct"] == 55.0
    assert row_2022["shots_faced"] != row_2023["shots_faced"]


def test_unknown_player_returns_empty_with_same_columns():
    performances = _performances()
    rows = player_context_rows(performances, "Nobody")
    assert rows.empty
    assert list(rows.columns) == list(performances.columns)


def test_none_player_returns_empty():
    rows = player_context_rows(_performances(), None)
    assert rows.empty


def test_empty_performances_returns_empty():
    empty = pd.DataFrame(columns=["player_name", "competition_id", "season_id", "minutes"])
    rows = player_context_rows(empty, "Keeper A")
    assert rows.empty
