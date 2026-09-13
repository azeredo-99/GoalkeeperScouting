"""
Testes de segurança de proveniência: garantem que dados StatsBomb
(source="statsbomb") e FBref (source="fbref") nunca se misturam num
peer group / cálculo de similaridade sem isso ser explícito, e que
ausência de dado FBref nunca é tratada como 0 nesses cálculos.

Não testa a ingestão em si (ver test_fbref_mapping.py) -- testa que o
código de leitura já existente (benchmarking.py, similarity_engine.py,
NENHUM DOS DOIS ALTERADO) se comporta corretamente quando a tabela tem
as duas proveniências lado a lado, que é o estado real da BD depois da
ingestão FBref.
"""

import pandas as pd
import pytest

from gk_scouting.benchmarking import BENCHMARK_METRICS, peer_pool
from gk_scouting.fbref_mapping import FBREF_COMPETITIONS, FBREF_SEASON_ID
from gk_scouting.similarity_engine import STYLE_FEATURES, find_similar_goalkeepers

# IDs StatsBomb realmente em uso (ver Data Coverage / auditoria de
# ingestão) -- a garantia de não-mistura depende estruturalmente de
# nenhum destes coincidir com um ID sintético FBref.
_STATSBOMB_COMPETITION_IDS = {43, 1267, 55, 7, 11, 9, 44, 16, 2, 12}
_STATSBOMB_SEASON_IDS = {27, 90, 106, 107, 235, 281, 282, 3, 4}


# ===========================================================================
# Garantia estrutural: IDs sintéticos FBref nunca colidem com StatsBomb
# ===========================================================================

def test_fbref_competition_ids_never_collide_with_statsbomb_ids():
    fbref_ids = {competition_id for competition_id, _name in FBREF_COMPETITIONS.values()}
    assert fbref_ids.isdisjoint(_STATSBOMB_COMPETITION_IDS)


def test_fbref_season_id_never_collides_with_a_statsbomb_season_id():
    assert FBREF_SEASON_ID not in _STATSBOMB_SEASON_IDS


# ===========================================================================
# peer_pool (benchmarking.py, inalterado) -- comportamento real com uma
# tabela que já tem as duas proveniências, tal como fica em produção.
# ===========================================================================

def _mixed_source_performances():
    statsbomb_cid, statsbomb_sid = 11, 27  # La Liga 2015/16, real
    fbref_cid, fbref_sid = list(FBREF_COMPETITIONS.values())[0][0], FBREF_SEASON_ID

    metric_columns = [column for _key, column, _label, _category in BENCHMARK_METRICS]

    def row(player_name, competition_id, season_id, minutes, source, metric_value):
        r = {
            "player_name": player_name, "competition_id": competition_id,
            "season_id": season_id, "minutes": minutes, "source": source,
        }
        for column in metric_columns:
            r[column] = metric_value
        return r

    rows = [
        row("SB Keeper A", statsbomb_cid, statsbomb_sid, 900, "statsbomb", 70.0),
        row("SB Keeper B", statsbomb_cid, statsbomb_sid, 900, "statsbomb", 75.0),
        row("SB Keeper C", statsbomb_cid, statsbomb_sid, 900, "statsbomb", 80.0),
        row("FBref Keeper A", fbref_cid, fbref_sid, 900, "fbref", 60.0),
        row("FBref Keeper B", fbref_cid, fbref_sid, 900, "fbref", 65.0),
        row("FBref Keeper C", fbref_cid, fbref_sid, 900, "fbref", 68.0),
    ]
    return pd.DataFrame(rows), (statsbomb_cid, statsbomb_sid), (fbref_cid, fbref_sid)


def test_peer_pool_for_a_statsbomb_context_never_includes_fbref_rows():
    performances, (sb_cid, sb_sid), _fbref = _mixed_source_performances()
    pool = peer_pool(performances, "SB Keeper A", sb_cid, sb_sid, min_minutes=450)
    assert set(pool["source"]) == {"statsbomb"}
    assert len(pool) == 2  # os outros dois SB keepers, nunca os FBref


def test_peer_pool_for_an_fbref_context_never_includes_statsbomb_rows():
    performances, _sb, (fbref_cid, fbref_sid) = _mixed_source_performances()
    pool = peer_pool(performances, "FBref Keeper A", fbref_cid, fbref_sid, min_minutes=450)
    assert set(pool["source"]) == {"fbref"}
    assert len(pool) == 2


# ===========================================================================
# similarity_engine (inalterado) -- ausência de dado FBref (None/NaN)
# nunca é tratada como 0 nem entra silenciosamente no cálculo.
# ===========================================================================

def _mixed_similarity_table():
    """
    2 guarda-redes StatsBomb com as 6 STYLE_FEATURES completas, 2
    guarda-redes FBref com só save_pct preenchido (as outras 5 são
    None, tal como fbref_mapping.fbref_row_to_gk_performance produz de
    facto para esta fonte).
    """
    full = {
        "sweeper_actions_p90": 1.2, "avg_distance_from_goal": 15.0,
        "save_pct": 70.0, "pass_success_pct": 60.0,
        "avg_pass_length": 30.0, "long_ball_pct": 40.0, "minutes": 2000,
    }
    fbref_only_save_pct = {
        "sweeper_actions_p90": None, "avg_distance_from_goal": None,
        "save_pct": 68.0, "pass_success_pct": None,
        "avg_pass_length": None, "long_ball_pct": None, "minutes": 2000,
    }

    table = pd.DataFrame(
        {
            "SB Keeper A": full,
            "SB Keeper B": {**full, "save_pct": 72.0},
            "FBref Keeper A": fbref_only_save_pct,
            "FBref Keeper B": {**fbref_only_save_pct, "save_pct": 69.0},
        }
    ).T
    table.index.name = "player"
    return table


def test_similarity_pool_drops_fbref_rows_missing_style_features_instead_of_treating_none_as_zero():
    table = _mixed_similarity_table()
    result = find_similar_goalkeepers(
        table, "SB Keeper A", top_n=10, features=STYLE_FEATURES, min_minutes=0,
    )
    # As duas linhas FBref não têm 5 das 6 features -- dropna(subset=...)
    # tem de as excluir do pool, nunca compará-las com None convertido a 0.
    assert "FBref Keeper A" not in result.index
    assert "FBref Keeper B" not in result.index
    assert "SB Keeper B" in result.index
