"""
Testes das funções puras do Performance Benchmark (`gk_scouting.benchmarking`).

Cobrem só o que é novo nesta fase: exclusão do próprio jogador do peer
pool, average-rank tie handling no percentile, os três tiers de amostra
(insufficient/small/normal), valor do jogador em falta (N/A, nunca 0th
percentile) e contagem de pares específica por métrica quando essa
métrica tem missing values reais (sweeping).
"""

import pandas as pd
import pytest

from gk_scouting.benchmarking import (
    build_benchmark,
    peer_pool,
    percentile_rank,
)


def _row(name, minutes, save_pct=None, sweeper_actions_p90=None,
         avg_distance_from_goal=None, pass_success_pct=None, long_ball_pct=None,
         competition_id=1, season_id=2024):
    return {
        "player_name": name,
        "competition_id": competition_id,
        "season_id": season_id,
        "minutes": minutes,
        "save_pct": save_pct,
        "sweeper_actions_p90": sweeper_actions_p90,
        "avg_distance_from_goal": avg_distance_from_goal,
        "pass_success_pct": pass_success_pct,
        "long_ball_pct": long_ball_pct,
    }


# ===========================================================================
# percentile_rank
# ===========================================================================

def test_percentile_rank_strictly_above_all_peers():
    assert percentile_rank(90.0, [70.0, 75.0, 80.0]) == 100.0


def test_percentile_rank_strictly_below_all_peers():
    assert percentile_rank(10.0, [70.0, 75.0, 80.0]) == 0.0


def test_percentile_rank_uses_average_rank_for_ties():
    # Empatado com 2 dos 4 pares: (0 abaixo + 0.5*2) / 4 * 100 = 25.0
    assert percentile_rank(50.0, [50.0, 50.0, 60.0, 70.0]) == 25.0


def test_percentile_rank_empty_peers_is_none():
    assert percentile_rank(50.0, []) is None


# ===========================================================================
# peer_pool
# ===========================================================================

def test_peer_pool_excludes_self():
    performances = pd.DataFrame([
        _row("Diogo Costa", 500, save_pct=80.0),
        _row("Keeper B", 500, save_pct=70.0),
    ])
    pool = peer_pool(performances, "Diogo Costa", 1, 2024, min_minutes=450)
    assert list(pool["player_name"]) == ["Keeper B"]


def test_peer_pool_respects_minimum_minutes_and_context():
    performances = pd.DataFrame([
        _row("Diogo Costa", 500, save_pct=80.0),
        _row("Below threshold", 300, save_pct=70.0),
        _row("Other competition", 500, save_pct=70.0, competition_id=2),
    ])
    pool = peer_pool(performances, "Diogo Costa", 1, 2024, min_minutes=450)
    assert pool.empty


# ===========================================================================
# build_benchmark -- sample tiers
# ===========================================================================

def _context_with_n_peers(n, target_value=80.0):
    rows = [_row("Target", 500, save_pct=target_value)]
    for i in range(n):
        rows.append(_row(f"Peer {i}", 500, save_pct=60.0 + i))
    return pd.DataFrame(rows)


def test_insufficient_sample_below_five_peers_has_no_percentile():
    performances = _context_with_n_peers(4)
    result = build_benchmark(performances, "Target", 1, 2024)
    save_pct = next(m for m in result["metrics"] if m["key"] == "save_pct")
    assert save_pct["status"] == "insufficient"
    assert save_pct["percentile"] is None
    assert save_pct["peerCount"] == 4


def test_small_sample_between_five_and_nine_peers_still_shows_percentile():
    performances = _context_with_n_peers(7)
    result = build_benchmark(performances, "Target", 1, 2024)
    save_pct = next(m for m in result["metrics"] if m["key"] == "save_pct")
    assert save_pct["status"] == "small"
    assert save_pct["percentile"] is not None
    assert save_pct["peerCount"] == 7


def test_normal_sample_at_ten_or_more_peers():
    performances = _context_with_n_peers(10)
    result = build_benchmark(performances, "Target", 1, 2024)
    save_pct = next(m for m in result["metrics"] if m["key"] == "save_pct")
    assert save_pct["status"] == "normal"
    assert save_pct["peerCount"] == 10


def test_available_flag_reflects_total_peer_pool_size():
    assert build_benchmark(_context_with_n_peers(4), "Target", 1, 2024)["available"] is False
    assert build_benchmark(_context_with_n_peers(5), "Target", 1, 2024)["available"] is True


# ===========================================================================
# build_benchmark -- missing data honesty
# ===========================================================================

def test_missing_player_value_is_no_data_never_zeroth_percentile():
    performances = _context_with_n_peers(7, target_value=None)
    result = build_benchmark(performances, "Target", 1, 2024)
    save_pct = next(m for m in result["metrics"] if m["key"] == "save_pct")
    assert save_pct["status"] == "no_data"
    assert save_pct["value"] is None
    assert save_pct["percentile"] is None


def test_metric_specific_peer_count_excludes_missing_values():
    # 7 pares com save_pct, mas só 3 com sweeper_actions_p90 (sweeping tem
    # missing values reais quando ninguém saiu da baliza) -- os peer
    # counts das duas métricas têm de divergir, nunca partilhar um N geral.
    rows = [_row("Target", 500, save_pct=80.0, sweeper_actions_p90=1.0)]
    for i in range(7):
        sweeper = 0.5 + i if i < 3 else None
        rows.append(_row(f"Peer {i}", 500, save_pct=60.0 + i, sweeper_actions_p90=sweeper))
    performances = pd.DataFrame(rows)

    result = build_benchmark(performances, "Target", 1, 2024)
    save_pct = next(m for m in result["metrics"] if m["key"] == "save_pct")
    sweeper = next(m for m in result["metrics"] if m["key"] == "sweeper_actions_p90")

    assert save_pct["peerCount"] == 7
    assert sweeper["peerCount"] == 3
    assert sweeper["status"] == "insufficient"
    assert sweeper["percentile"] is None


def test_target_not_found_returns_no_data_for_every_metric():
    performances = _context_with_n_peers(7)
    result = build_benchmark(performances, "Unknown Player", 1, 2024)
    assert all(m["status"] == "no_data" for m in result["metrics"])
