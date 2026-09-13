"""
Testes de gk_scouting.fbref_mapping -- transformação pura (sem I/O de
rede nem de BD) das estatísticas de guarda-redes do FBref para o schema
de gk_performances.
"""

import math

import pandas as pd
import pytest

from gk_scouting.fbref_mapping import (
    FBREF_COMPETITIONS,
    FBREF_SEASON_ID,
    GK_PERFORMANCE_COLUMNS,
    aggregate_multi_club_rows,
    build_fbref_table,
    fbref_row_to_gk_performance,
    load_raw_keeper_csv,
)

_NEVER_AVAILABLE = [
    "sweeper_actions", "sweeper_actions_p90", "avg_distance_from_goal",
    "max_distance_from_goal", "total_passes", "pass_success_pct",
    "avg_pass_length", "long_ball_pct",
]


# ===========================================================================
# load_raw_keeper_csv -- parsing do cabeçalho real de duas linhas
# ===========================================================================

def _write_raw_csv(tmp_path, rows):
    """
    Constrói um CSV com exatamente a forma real confirmada na auditoria:
    cabeçalho de dois níveis (grupo / métrica) + índice
    (league, season, team, player). `rows` é uma lista de dicts com as
    chaves de nível de métrica (ex. "Min", "SoTA", "Save%").
    """
    columns = pd.MultiIndex.from_tuples(
        [
            ("", "league"), ("", "season"), ("", "team"), ("", "player"),
            ("nation", ""), ("pos", ""), ("age", ""), ("born", ""),
            ("Playing Time", "MP"), ("Playing Time", "Starts"),
            ("Playing Time", "Min"), ("Playing Time", "90s"),
            ("Performance", "GA"), ("Performance", "GA90"),
            ("Performance", "SoTA"), ("Performance", "Saves"),
            ("Performance", "Save%"), ("Performance", "W"),
            ("Performance", "D"), ("Performance", "L"),
            ("Performance", "CS"), ("Performance", "CS%"),
            ("Penalty Kicks", "PKatt"), ("Penalty Kicks", "PKA"),
            ("Penalty Kicks", "PKsv"), ("Penalty Kicks", "PKm"),
            ("Penalty Kicks", "Save%"),
        ]
    )
    data = []
    for r in rows:
        data.append([
            r["league"], r["season"], r["team"], r["player"],
            "ENG", "GK", 28, 1995,
            r.get("MP", 10), r.get("Starts", 10), r["Min"], r.get("90s", r["Min"] / 90),
            r["GA"], r.get("GA90", 0), r["SoTA"], r["Saves"], r.get("Save%", None),
            r.get("W", 0), r.get("D", 0), r.get("L", 0),
            r.get("CS", 0), r.get("CS%", 0),
            r.get("PKatt", 0), r.get("PKA", 0), r.get("PKsv", 0), r.get("PKm", 0),
            r.get("PK_Save%", None),
        ])
    df = pd.DataFrame(data, columns=columns)
    df = df.set_index([("", "league"), ("", "season"), ("", "team"), ("", "player")])
    df.index.names = ["league", "season", "team", "player"]

    path = tmp_path / "sample_keeper.csv"
    df.to_csv(path)
    return path


def test_load_raw_keeper_csv_disambiguates_the_two_save_pct_columns(tmp_path):
    path = _write_raw_csv(
        tmp_path,
        [dict(league="ENG-Premier League", season="2425", team="Arsenal", player="David Raya",
              Min=3420, GA=34, SoTA=120, Saves=86, **{"Save%": 71.7, "PK_Save%": 0.0})],
    )
    df = load_raw_keeper_csv(path)
    assert "Save%" in df.columns
    assert "PK_Save%" in df.columns
    assert df.loc[0, "Save%"] == 71.7
    assert df.loc[0, "PK_Save%"] == 0.0


def test_load_raw_keeper_csv_recovers_identity_columns(tmp_path):
    path = _write_raw_csv(
        tmp_path,
        [dict(league="ENG-Premier League", season="2425", team="Arsenal", player="David Raya",
              Min=3420, GA=34, SoTA=120, Saves=86)],
    )
    df = load_raw_keeper_csv(path)
    # "season" faz roundtrip como inteiro (2425), não como string --
    # sem impacto na pipeline real, que nunca lê esta coluna (usa
    # sempre FBREF_SEASON_ID). As restantes ficam como texto.
    assert df.loc[0, "league"] == "ENG-Premier League"
    assert df.loc[0, "team"] == "Arsenal"
    assert df.loc[0, "player"] == "David Raya"


# ===========================================================================
# aggregate_multi_club_rows
# ===========================================================================

def _raw_frame(rows):
    return pd.DataFrame(rows)


def test_single_club_player_passes_through_unchanged():
    df = _raw_frame([
        {"league": "ENG-Premier League", "season": "2425", "team": "Arsenal", "player": "David Raya",
         "MP": 38, "Starts": 38, "90s": 38.0, "Min": 3420, "GA": 34, "SoTA": 120, "Saves": 86,
         "Save%": 71.7, "W": 20, "D": 14, "L": 4, "PKatt": 3, "PKA": 3, "PKsv": 0, "PKm": 0},
    ])
    result = aggregate_multi_club_rows(df)
    assert len(result) == 1
    assert result.iloc[0]["Save%"] == 71.7  # não recalculado -- é a única linha
    assert result.iloc[0]["team"] == "Arsenal"


def test_multi_club_player_is_merged_into_a_single_row():
    """
    Réplica do caso real confirmado na auditoria: Brice Samba,
    Lens -> Rennes, Ligue 1 2024/25.
    """
    df = _raw_frame([
        {"league": "FRA-Ligue 1", "season": "2425", "team": "Lens", "player": "Brice Samba",
         "MP": 15, "Starts": 15, "90s": 15.0, "Min": 1350, "GA": 15, "SoTA": 50, "Saves": 35,
         "Save%": 70.0, "W": 8, "D": 4, "L": 3, "PKatt": 1, "PKA": 1, "PKsv": 0, "PKm": 0},
        {"league": "FRA-Ligue 1", "season": "2425", "team": "Rennes", "player": "Brice Samba",
         "MP": 17, "Starts": 17, "90s": 17.0, "Min": 1529, "GA": 20, "SoTA": 60, "Saves": 40,
         "Save%": 66.7, "W": 7, "D": 5, "L": 5, "PKatt": 2, "PKA": 1, "PKsv": 1, "PKm": 0},
    ])
    result = aggregate_multi_club_rows(df)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["player"] == "Brice Samba"
    assert row["team"] == "Multiple clubs"
    assert row["Min"] == 1350 + 1529
    assert row["GA"] == 15 + 20
    assert row["SoTA"] == 50 + 60
    assert row["Saves"] == 35 + 40
    assert row["PKatt"] == 1 + 2


def test_multi_club_save_pct_is_recomputed_from_summed_totals_not_averaged():
    """
    70.0 e 66.7 têm média simples 68.35 -- mas a percentagem CORRETA
    combinada é (35+40)/(50+60)*100 = 68.18(3)%. Se o código estivesse a
    fazer média das percentagens em vez de recalcular a partir dos
    totais, este teste apanhava isso.
    """
    df = _raw_frame([
        {"league": "FRA-Ligue 1", "season": "2425", "team": "Lens", "player": "Brice Samba",
         "Min": 1350, "GA": 15, "SoTA": 50, "Saves": 35, "Save%": 70.0,
         "MP": 15, "Starts": 15, "90s": 15.0, "W": 0, "D": 0, "L": 0, "PKatt": 0, "PKA": 0, "PKsv": 0, "PKm": 0},
        {"league": "FRA-Ligue 1", "season": "2425", "team": "Rennes", "player": "Brice Samba",
         "Min": 1529, "GA": 20, "SoTA": 60, "Saves": 40, "Save%": 66.7,
         "MP": 17, "Starts": 17, "90s": 17.0, "W": 0, "D": 0, "L": 0, "PKatt": 0, "PKA": 0, "PKsv": 0, "PKm": 0},
    ])
    result = aggregate_multi_club_rows(df)
    expected = (35 + 40) / (50 + 60) * 100
    assert result.iloc[0]["Save%"] == pytest.approx(expected)
    assert result.iloc[0]["Save%"] != pytest.approx((70.0 + 66.7) / 2)


def test_multi_club_with_zero_combined_sota_gives_none_save_pct_not_zero():
    df = _raw_frame([
        {"league": "ITA-Serie A", "season": "2425", "team": "A", "player": "Backup Keeper",
         "Min": 45, "GA": 0, "SoTA": 0, "Saves": 0, "Save%": None,
         "MP": 1, "Starts": 0, "90s": 0.5, "W": 0, "D": 0, "L": 0, "PKatt": 0, "PKA": 0, "PKsv": 0, "PKm": 0},
        {"league": "ITA-Serie A", "season": "2425", "team": "B", "player": "Backup Keeper",
         "Min": 45, "GA": 0, "SoTA": 0, "Saves": 0, "Save%": None,
         "MP": 1, "Starts": 0, "90s": 0.5, "W": 0, "D": 0, "L": 0, "PKatt": 0, "PKA": 0, "PKsv": 0, "PKm": 0},
    ])
    result = aggregate_multi_club_rows(df)
    assert result.iloc[0]["Save%"] is None


# ===========================================================================
# fbref_row_to_gk_performance
# ===========================================================================

def _row(**overrides):
    base = {
        "league": "ENG-Premier League", "player": "David Raya",
        "Min": 3420.0, "SoTA": 120.0, "Saves": 86.0, "GA": 34.0, "Save%": 71.7,
    }
    base.update(overrides)
    return pd.Series(base)


def test_maps_direct_fields_correctly():
    record = fbref_row_to_gk_performance(_row())
    assert record["minutes"] == 3420.0
    assert record["shots_faced"] == 120.0
    assert record["shots_saved"] == 86.0
    assert record["goals_conceded"] == 34.0
    assert record["save_pct"] == 71.7
    assert record["source"] == "fbref"


def test_shots_faced_p90_is_computed_not_taken_from_ga90():
    record = fbref_row_to_gk_performance(_row(Min=3420.0, SoTA=120.0))
    assert record["shots_faced_p90"] == pytest.approx(120.0 / 3420.0 * 90.0)


def test_shots_faced_p90_is_none_when_minutes_is_zero():
    record = fbref_row_to_gk_performance(_row(Min=0.0))
    assert record["shots_faced_p90"] is None


def test_never_available_fields_are_none_not_zero():
    record = fbref_row_to_gk_performance(_row())
    for field in _NEVER_AVAILABLE:
        assert record[field] is None


def test_missing_save_pct_becomes_none_not_nan():
    record = fbref_row_to_gk_performance(_row(**{"Save%": float("nan")}))
    assert record["save_pct"] is None


def test_unknown_league_raises_value_error():
    with pytest.raises(ValueError, match="Liga FBref desconhecida"):
        fbref_row_to_gk_performance(_row(league="XXX-Not A League"))


def test_competition_id_matches_fbref_competitions_registry():
    for league, (competition_id, _name) in FBREF_COMPETITIONS.items():
        record = fbref_row_to_gk_performance(_row(league=league))
        assert record["competition_id"] == competition_id
        assert record["season_id"] == FBREF_SEASON_ID


# ===========================================================================
# build_fbref_table -- integração da pipeline pura, ponta a ponta
# ===========================================================================

def test_build_fbref_table_shape_and_index(tmp_path):
    import gk_scouting.fbref_mapping as fbref_mapping

    (tmp_path / "sample").mkdir()
    d = tmp_path / "sample"

    # Escreve os 5 ficheiros esperados, cada um com 1 guarda-redes, para
    # exercitar a pipeline completa sem depender dos CSVs reais.
    for filename, league in zip(
        fbref_mapping.RAW_CSV_FILES,
        ["ENG-Premier League", "ESP-La Liga", "GER-Bundesliga", "ITA-Serie A", "FRA-Ligue 1"],
    ):
        path = _write_raw_csv(
            tmp_path,
            [dict(league=league, season="2425", team="Some Club", player=f"Keeper {league}",
                  Min=1000, GA=10, SoTA=40, Saves=30, **{"Save%": 75.0})],
        )
        path.rename(d / filename)

    table = fbref_mapping.build_fbref_table(d)

    assert list(table.index.names) == ["player", "competition_id", "season_id"]
    assert list(table.columns) == GK_PERFORMANCE_COLUMNS
    assert len(table) == 5
    assert (table["source"] == "fbref").all()
    assert set(table.index.get_level_values("season_id")) == {FBREF_SEASON_ID}
