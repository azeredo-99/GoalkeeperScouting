"""
Testes das funções puras do modo Discovery (Fase 3 do roadmap de
produto): pesquisa por nome, enriquecimento com dados de mercado e
filtros de descoberta por perfil.

Não testam UI/Streamlit -- só a lógica de `gk_scouting.discovery`, que é
pura e não depende de BD nem de sessão do Streamlit.
"""

import math

import pandas as pd
import pytest

from gk_scouting.discovery import (
    available_competitions,
    available_seasons,
    enrich_with_market,
    filter_candidates,
    search_by_name,
)


def _performances():
    """
    Três jogadores, um deles (Keeper A) em duas competições/épocas
    diferentes, com valores propositadamente distintos para que uma
    mistura acidental entre contextos seja detetável.
    """
    return pd.DataFrame(
        [
            {"player_name": "Diogo Costa", "competition_id": 1, "season_id": 2022,
             "minutes": 900.0, "save_pct": 80.0},
            {"player_name": "Diogo Costa", "competition_id": 2, "season_id": 2023,
             "minutes": 300.0, "save_pct": 55.0},
            {"player_name": "Thibaut Courtois", "competition_id": 1, "season_id": 2022,
             "minutes": 600.0, "save_pct": 70.0},
            {"player_name": "Yassine Bounou", "competition_id": 3, "season_id": 2021,
             "minutes": 120.0, "save_pct": 65.0},
        ]
    )


# ===========================================================================
# search_by_name
# ===========================================================================

def test_search_is_case_insensitive():
    result = search_by_name(_performances(), "diogo costa")
    assert set(result["player_name"]) == {"Diogo Costa"}


def test_search_is_partial():
    result = search_by_name(_performances(), "cost")
    assert set(result["player_name"]) == {"Diogo Costa"}


def test_search_uppercase_query_matches_mixed_case_name():
    result = search_by_name(_performances(), "COURTOIS")
    assert set(result["player_name"]) == {"Thibaut Courtois"}


def test_search_with_no_match_returns_empty():
    result = search_by_name(_performances(), "Nonexistent Keeper")
    assert result.empty


def test_search_with_empty_query_returns_empty_not_everything():
    """Pesquisa vazia não deve devolver a tabela inteira."""
    result = search_by_name(_performances(), "")
    assert result.empty


def test_search_with_whitespace_only_query_returns_empty():
    result = search_by_name(_performances(), "   ")
    assert result.empty


def test_search_returns_every_context_row_not_aggregated():
    """
    Requisito central: um jogador com várias competições/épocas aparece
    em várias linhas de resultado, cada uma com o seu próprio contexto.
    """
    result = search_by_name(_performances(), "Diogo Costa")
    assert len(result) == 2
    assert set(zip(result["competition_id"], result["season_id"])) == {
        (1, 2022),
        (2, 2023),
    }
    # Os valores não podem estar misturados entre os dois contextos.
    row_2022 = result[result["season_id"] == 2022].iloc[0]
    row_2023 = result[result["season_id"] == 2023].iloc[0]
    assert row_2022["save_pct"] == 80.0
    assert row_2023["save_pct"] == 55.0


def test_search_preserves_competition_and_season_columns():
    result = search_by_name(_performances(), "Bounou")
    row = result.iloc[0]
    assert row["competition_id"] == 3
    assert row["season_id"] == 2021


def test_search_on_empty_performances_returns_empty():
    empty = pd.DataFrame(columns=["player_name", "competition_id", "season_id", "minutes"])
    result = search_by_name(empty, "Diogo")
    assert result.empty


# ===========================================================================
# enrich_with_market
# ===========================================================================

def _market_lookup():
    return {
        "Diogo Costa": pd.Series(
            {"current_club_name": "FC Porto", "market_value_in_eur": 40_000_000.0,
             "date_of_birth": "1999-09-19"}
        ),
        "Thibaut Courtois": pd.Series(
            {"current_club_name": "Real Madrid", "market_value_in_eur": 15_000_000.0,
             "date_of_birth": "1992-05-11"}
        ),
    }


def test_enrich_adds_club_value_and_age_columns():
    enriched = enrich_with_market(_performances(), _market_lookup())
    row = enriched[enriched["player_name"] == "Diogo Costa"].iloc[0]
    assert row["current_club_name"] == "FC Porto"
    assert row["market_value_in_eur"] == 40_000_000.0
    assert row["age"] is not None


def test_enrich_does_not_mix_up_players():
    enriched = enrich_with_market(_performances(), _market_lookup())
    courtois = enriched[enriched["player_name"] == "Thibaut Courtois"].iloc[0]
    assert courtois["current_club_name"] == "Real Madrid"
    assert courtois["market_value_in_eur"] == 15_000_000.0


def test_enrich_player_without_market_match_gets_none_not_invented_data():
    """
    Bounou não está no lookup -- os campos de mercado ficam ausentes
    (None/NaN, consoante a coerção do pandas no `.map()`), nunca um
    valor inventado. `pd.isna` é a verificação usada em todo o projeto
    para "ausente" (ver `presentation.format_metric`).
    """
    enriched = enrich_with_market(_performances(), _market_lookup())
    row = enriched[enriched["player_name"] == "Yassine Bounou"].iloc[0]
    assert pd.isna(row["current_club_name"])
    assert pd.isna(row["market_value_in_eur"])
    assert pd.isna(row["age"])


def test_enrich_on_empty_dataframe_returns_empty_with_expected_columns():
    empty = pd.DataFrame(columns=["player_name", "competition_id", "season_id", "minutes"])
    enriched = enrich_with_market(empty, _market_lookup())
    assert enriched.empty
    for column in ("current_club_name", "market_value_in_eur", "age"):
        assert column in enriched.columns


# ===========================================================================
# filter_candidates
# ===========================================================================

def _enriched():
    return enrich_with_market(_performances(), _market_lookup())


def test_filter_by_competition_id():
    result = filter_candidates(_enriched(), competition_id=1)
    assert set(result["player_name"]) == {"Diogo Costa", "Thibaut Courtois"}


def test_filter_by_season_id():
    result = filter_candidates(_enriched(), season_id=2023)
    assert len(result) == 1
    assert result.iloc[0]["player_name"] == "Diogo Costa"
    assert result.iloc[0]["season_id"] == 2023


def test_filter_by_minimum_minutes():
    result = filter_candidates(_enriched(), min_minutes=500)
    assert set(result["player_name"]) == {"Diogo Costa", "Thibaut Courtois"}
    assert all(result["minutes"] >= 500)


def test_filter_no_criteria_returns_everything_unchanged():
    """None em todos os filtros = 'todas as competições/épocas', explícito."""
    result = filter_candidates(_enriched())
    assert len(result) == len(_enriched())


def test_combination_of_filters():
    result = filter_candidates(
        _enriched(),
        competition_id=1,
        min_minutes=700,
    )
    assert set(result["player_name"]) == {"Diogo Costa"}


def test_incompatible_filters_return_no_results():
    result = filter_candidates(
        _enriched(),
        competition_id=1,
        season_id=2023,  # não existe combinação (1, 2023) nos dados
    )
    assert result.empty


def test_filter_preserves_competition_and_season_columns():
    result = filter_candidates(_enriched(), competition_id=1)
    assert "competition_id" in result.columns
    assert "season_id" in result.columns
    assert set(result["competition_id"]) == {1}


# --- idade e valor de mercado: só filtram quem tem o dado ---

def test_filter_by_max_age_excludes_players_without_known_age():
    """
    Bounou não tem correspondência de mercado (sem idade conhecida) --
    um filtro de idade ativo tem de o excluir, não incluir por omissão.
    """
    result = filter_candidates(_enriched(), max_age=100)
    assert "Yassine Bounou" not in set(result["player_name"])


def test_filter_by_max_age_keeps_players_within_the_limit():
    enriched = _enriched()
    # Idade calculada a partir de date_of_birth -- só precisamos saber
    # que é um número finito e que o filtro com limite muito alto não
    # exclui ninguém que tenha idade conhecida.
    result = filter_candidates(enriched, max_age=200)
    known_age_players = {"Diogo Costa", "Thibaut Courtois"}
    assert known_age_players.issubset(set(result["player_name"]))


def test_filter_by_max_market_value():
    result = filter_candidates(_enriched(), max_market_value=20_000_000.0)
    assert set(result["player_name"]) == {"Thibaut Courtois"}


def test_filter_by_min_market_value():
    result = filter_candidates(_enriched(), min_market_value=20_000_000.0)
    assert set(result["player_name"]) == {"Diogo Costa"}


def test_market_value_filter_excludes_players_without_market_data():
    result = filter_candidates(_enriched(), min_market_value=0.0)
    assert "Yassine Bounou" not in set(result["player_name"])


# ===========================================================================
# available_competitions / available_seasons
# ===========================================================================

def test_available_competitions_lists_distinct_values_sorted():
    assert available_competitions(_performances()) == [1, 2, 3]


def test_available_competitions_on_empty_returns_empty_list():
    empty = pd.DataFrame(columns=["competition_id"])
    assert available_competitions(empty) == []


def test_available_seasons_without_competition_filter():
    assert available_seasons(_performances()) == [2021, 2022, 2023]


def test_available_seasons_restricted_to_one_competition():
    """Só as épocas que existem de facto para essa competição."""
    result = available_seasons(_performances(), competition_id=1)
    assert result == [2022]
