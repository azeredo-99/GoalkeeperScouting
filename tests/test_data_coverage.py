"""Testes de `gk_scouting.data_coverage` -- contagens reais, sem números inventados."""

import pandas as pd

from gk_scouting.data_coverage import build_coverage


def _performances():
    rows = [{"player_name": f"Strong {i}", "competition_id": 1, "season_id": 2024, "minutes": 900.0} for i in range(10)]
    rows += [{"player_name": f"Partial {i}", "competition_id": 2, "season_id": 2024, "minutes": 900.0} for i in range(6)]
    rows += [{"player_name": f"Limited {i}", "competition_id": 3, "season_id": 2024, "minutes": 900.0} for i in range(2)]
    rows += [{"player_name": "Below threshold", "competition_id": 4, "season_id": 2024, "minutes": 100.0}]
    return pd.DataFrame(rows)


def test_coverage_on_empty_performances_returns_empty_list():
    empty = pd.DataFrame(columns=["player_name", "competition_id", "season_id", "minutes"])
    assert build_coverage(empty) == []


def test_status_strong_at_ten_or_more_benchmarkable():
    rows = build_coverage(_performances(), min_minutes=450)
    strong = next(r for r in rows if r["competition_id"] == 1)
    assert strong["benchmarkable_goalkeepers"] == 10
    assert strong["status"] == "strong"


def test_status_partial_between_five_and_nine():
    rows = build_coverage(_performances(), min_minutes=450)
    partial = next(r for r in rows if r["competition_id"] == 2)
    assert partial["benchmarkable_goalkeepers"] == 6
    assert partial["status"] == "partial"


def test_status_limited_between_one_and_four():
    rows = build_coverage(_performances(), min_minutes=450)
    limited = next(r for r in rows if r["competition_id"] == 3)
    assert limited["benchmarkable_goalkeepers"] == 2
    assert limited["status"] == "limited"


def test_status_insufficient_when_zero_benchmarkable():
    rows = build_coverage(_performances(), min_minutes=450)
    insufficient = next(r for r in rows if r["competition_id"] == 4)
    assert insufficient["benchmarkable_goalkeepers"] == 0
    assert insufficient["total_goalkeepers"] == 1
    assert insufficient["status"] == "insufficient"


def test_coverage_sorted_by_benchmarkable_descending():
    rows = build_coverage(_performances(), min_minutes=450)
    counts = [r["benchmarkable_goalkeepers"] for r in rows]
    assert counts == sorted(counts, reverse=True)


def test_coverage_never_invents_a_context_not_in_the_data():
    rows = build_coverage(_performances(), min_minutes=450)
    contexts = {(r["competition_id"], r["season_id"]) for r in rows}
    assert contexts == {(1, 2024), (2, 2024), (3, 2024), (4, 2024)}
