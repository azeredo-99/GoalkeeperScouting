"""
Testes de `gk_scouting.comparison` (Fase 4 do roadmap de produto:
Comparação com contexto individual por jogador).

`build_comparison_table` é a única função pública -- monta a tabela de
comparação a partir de linhas de contexto já escolhidas (uma por
jogador), sem recalcular nem agregar nada.
"""

import numpy as np
import pandas as pd
import pytest

from gk_scouting.comparison import build_comparison_table


def _row(player_name, competition_id, season_id, minutes, **overrides):
    data = {
        "player_name": player_name,
        "competition_id": competition_id,
        "season_id": season_id,
        "minutes": minutes,
        "save_pct": np.nan,
        "sweeper_actions": np.nan,
    }
    data.update(overrides)
    return pd.Series(data)


def test_table_indexed_by_player_name():
    rows = [
        _row("Keeper A", 1, 2022, 900.0),
        _row("Keeper B", 2, 2023, 600.0),
    ]
    table = build_comparison_table(rows)
    assert list(table.index) == ["Keeper A", "Keeper B"]
    assert table.index.name == "player"


def test_players_keep_their_own_competition_and_season():
    """
    Requisito central: não assumir que todos os jogadores pertencem à
    mesma competição/época.
    """
    rows = [
        _row("Keeper A", 1, 2022, 900.0),
        _row("Keeper B", 7, 235, 600.0),
    ]
    table = build_comparison_table(rows)
    assert table.loc["Keeper A", "competition_id"] == 1
    assert table.loc["Keeper A", "season_id"] == 2022
    assert table.loc["Keeper B", "competition_id"] == 7
    assert table.loc["Keeper B", "season_id"] == 235


def test_selected_context_row_is_preserved_not_the_highest_minutes_one():
    """
    O ponto principal do pedido: a comparação usa a linha de contexto
    escolhida para cada jogador, mesmo que não seja a de mais minutos.
    Aqui simulamos que o utilizador escolheu, para o Keeper A, a
    competição 2 (300 min) e não a 1 (900 min, que teria mais minutos).
    """
    chosen_row = _row("Keeper A", 2, 2023, 300.0, save_pct=55.0)
    table = build_comparison_table([chosen_row, _row("Keeper B", 1, 2022, 600.0)])

    assert table.loc["Keeper A", "minutes"] == 300.0
    assert table.loc["Keeper A", "competition_id"] == 2
    assert table.loc["Keeper A", "save_pct"] == 55.0


def test_nan_metric_survives_untouched_not_converted_to_zero():
    rows = [_row("Keeper A", 1, 2022, 900.0, sweeper_actions=np.nan)]
    table = build_comparison_table(rows)
    assert pd.isna(table.loc["Keeper A", "sweeper_actions"])


def test_supports_between_two_and_four_players():
    rows = [
        _row("Keeper A", 1, 2022, 900.0),
        _row("Keeper B", 1, 2022, 800.0),
        _row("Keeper C", 2, 2023, 700.0),
        _row("Keeper D", 3, 2021, 600.0),
    ]
    table = build_comparison_table(rows)
    assert len(table) == 4


def test_none_rows_are_skipped_not_crashing():
    rows = [_row("Keeper A", 1, 2022, 900.0), None]
    table = build_comparison_table(rows)
    assert list(table.index) == ["Keeper A"]


def test_empty_rows_return_empty_dataframe():
    assert build_comparison_table([]).empty
    assert build_comparison_table([None, None]).empty
