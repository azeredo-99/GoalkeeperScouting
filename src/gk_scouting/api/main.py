"""
API mínima para o frontend React (Fase 6 do roadmap de produto).

Reutiliza integralmente a lógica já existente -- não recalcula nada:

    load_gk_performances()   -- gk_scouting.db.repository (P7)
    search_by_name / filter_candidates / enrich_with_market
                              -- gk_scouting.discovery (Fase 3)
    build_comparison_table   -- gk_scouting.comparison (Fase 4)
    build_similarity_rows    -- gk_scouting.similarity_view (Fase 4)
    find_similar_goalkeepers / explain_similarity / normalise_dimension_weights
                              -- gk_scouting.similarity_engine (inalterado)

Os dados carregam-se uma vez no arranque (mesma estratégia do
`streamlit_app.py`: `performances` completo + `table` colapsada por
jogador para o motor de similaridade, que exige índice único).
"""

import math
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from gk_scouting.db.repository import load_gk_performances
from gk_scouting.market_data import calculate_age, format_market_value, get_goalkeepers
from gk_scouting.player_matching import create_name_index, match_players
from gk_scouting.discovery import (
    available_competitions,
    available_seasons,
    enrich_with_market,
    filter_candidates,
    search_by_name,
)
from gk_scouting.comparison import build_comparison_table
from gk_scouting.presentation import player_context_rows
from gk_scouting.similarity_engine import (
    STYLE_FEATURES,
    default_min_minutes,
    explain_similarity,
    find_similar_goalkeepers,
)
from gk_scouting.similarity_view import build_similarity_rows, reference_context

app = FastAPI(title="Goalkeeper Scouting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev local apenas
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Dados carregados uma vez -- mesma estratégia de streamlit_app.py
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _state():
    performances = load_gk_performances()

    market_df = get_goalkeepers()
    market_df = create_name_index(market_df)

    matches = match_players(performances["player_name"].unique(), market_df)
    market_lookup = {}
    for _, row in matches.iterrows():
        if row["match_status"] != "matched":
            continue
        market_lookup[row["statsbomb_name"]] = row

    table = (
        performances.sort_values("minutes", ascending=False)
        .drop_duplicates(subset="player_name", keep="first")
        .set_index("player_name")
    )
    table.index.name = "player"

    return performances, table, market_lookup


def _clean(value):
    """NaN/None -> None para serialização JSON limpa (nunca 0)."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
        if isinstance(value, float) and math.isnan(value):
            return None
    return value


def _identity(player_name: str, market_lookup: dict) -> dict:
    market = market_lookup.get(player_name)
    if market is None:
        return {
            "playerName": player_name,
            "club": None,
            "age": None,
            "marketValueEur": None,
            "highestMarketValueEur": None,
        }
    return {
        "playerName": player_name,
        "club": _clean(market.get("current_club_name")),
        "age": calculate_age(market.get("date_of_birth")),
        "marketValueEur": _clean(market.get("market_value_in_eur")),
        "highestMarketValueEur": _clean(market.get("highest_market_value_in_eur")),
    }


def _row_to_dict(row: pd.Series, market_lookup: dict) -> dict:
    market = market_lookup.get(row["player_name"] if "player_name" in row else row.name)
    return {
        "playerName": row.get("player_name", row.name),
        "competitionId": int(row["competition_id"]),
        "seasonId": int(row["season_id"]),
        "minutes": _clean(row["minutes"]),
        "club": _clean(market.get("current_club_name")) if market is not None else None,
        "marketValueEur": _clean(market.get("market_value_in_eur")) if market is not None else None,
        "metrics": {
            "shotStopping": {
                "savePct": _clean(row.get("save_pct")),
                "shotsFaced": _clean(row.get("shots_faced")),
                "shotsSaved": _clean(row.get("shots_saved")),
                "goalsConceded": _clean(row.get("goals_conceded")),
                "shotsFacedP90": _clean(row.get("shots_faced_p90")),
            },
            "sweeping": {
                "sweeperActions": _clean(row.get("sweeper_actions")),
                "sweeperActionsP90": _clean(row.get("sweeper_actions_p90")),
                "avgDistanceFromGoal": _clean(row.get("avg_distance_from_goal")),
                "maxDistanceFromGoal": _clean(row.get("max_distance_from_goal")),
            },
            "distribution": {
                "passSuccessPct": _clean(row.get("pass_success_pct")),
                "totalPasses": _clean(row.get("total_passes")),
                "avgPassLength": _clean(row.get("avg_pass_length")),
                "longBallPct": _clean(row.get("long_ball_pct")),
            },
        },
    }


# ---------------------------------------------------------------------------
# Competitions / Seasons
# ---------------------------------------------------------------------------

@app.get("/api/competitions")
def get_competitions():
    performances, _, _ = _state()
    return {"competitions": available_competitions(performances)}


@app.get("/api/seasons")
def get_seasons(competition_id: int | None = None):
    performances, _, _ = _state()
    return {"seasons": available_seasons(performances, competition_id)}


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

@app.get("/api/players/search")
def search_players(q: str = Query(..., min_length=1)):
    performances, _, market_lookup = _state()
    matches = search_by_name(performances, q)
    return {"results": [_row_to_dict(row, market_lookup) for _, row in matches.iterrows()]}


@app.get("/api/players/discover")
def discover_players(
    competition_id: int | None = None,
    season_id: int | None = None,
    min_minutes: float | None = None,
    max_age: float | None = None,
    max_market_value_eur: float | None = None,
):
    performances, _, market_lookup = _state()
    enriched = enrich_with_market(performances, market_lookup)
    candidates = filter_candidates(
        enriched,
        competition_id=competition_id,
        season_id=season_id,
        min_minutes=min_minutes,
        max_age=max_age,
        max_market_value=max_market_value_eur,
    )
    return {"results": [_row_to_dict(row, market_lookup) for _, row in candidates.iterrows()]}


# ---------------------------------------------------------------------------
# Player Profile
# ---------------------------------------------------------------------------

@app.get("/api/players/{player_name}/performances")
def get_player_performances(player_name: str):
    performances, _, market_lookup = _state()
    rows = player_context_rows(performances, player_name)

    if rows.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    return {
        "identity": _identity(player_name, market_lookup),
        "performances": [_row_to_dict(row, market_lookup) for _, row in rows.iterrows()],
    }


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

@app.get("/api/comparison")
def get_comparison(selections: str = Query(..., description="name:competitionId:seasonId,...")):
    performances, _, market_lookup = _state()

    rows = []
    for chunk in selections.split(","):
        parts = chunk.rsplit(":", 2)
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail=f"Invalid selection: {chunk}")
        name, competition_id, season_id = parts
        match = performances[
            (performances["player_name"] == name)
            & (performances["competition_id"] == int(competition_id))
            & (performances["season_id"] == int(season_id))
        ]
        if match.empty:
            raise HTTPException(status_code=404, detail=f"No performance for {chunk}")
        rows.append(match.iloc[0])

    if len(rows) < 2 or len(rows) > 4:
        raise HTTPException(status_code=400, detail="Comparison requires 2 to 4 players")

    table = build_comparison_table(rows)
    return {"players": [_row_to_dict(row, market_lookup) for _, row in table.reset_index().assign(player_name=table.index).iterrows()]}


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

@app.get("/api/similarity")
def get_similarity(
    target: str,
    w_shot_stopping: float = 30,
    w_distribution: float = 35,
    w_proactivity: float = 35,
    min_minutes: float | None = None,
    top_n: int = 5,
):
    performances, table, market_lookup = _state()

    if target not in table.index:
        raise HTTPException(status_code=404, detail="Reference player not eligible (insufficient minutes)")

    context = reference_context(table, target)
    threshold = min_minutes if min_minutes is not None else default_min_minutes(table["minutes"])

    try:
        similar = find_similar_goalkeepers(
            table,
            target,
            top_n=max(top_n * 5, 30),
            features=STYLE_FEATURES,
            min_minutes=int(threshold),
            dimension_weights={
                "Shot Stopping": w_shot_stopping,
                "Distribution": w_distribution,
                "Proactivity": w_proactivity,
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    similar = similar.head(top_n)

    rows = build_similarity_rows(
        similar, table, target, market_lookup, explain_similarity, STYLE_FEATURES
    )

    return {
        "target": _identity(target, market_lookup) | {
            "competitionId": int(context["competition_id"]),
            "seasonId": int(context["season_id"]),
            "minutes": _clean(context["minutes"]),
        },
        "results": [
            {
                "rank": r["rank"],
                "playerName": r["player_name"],
                "competitionId": r["competition_id"],
                "seasonId": r["season_id"],
                "minutes": _clean(r["minutes"]),
                "club": r["current_club_name"],
                "marketValueEur": _clean(r["market_value_in_eur"]),
                "similarityPct": round(r["similarity_pct"], 1),
                "explanation": r["explanation"],
            }
            for r in rows
        ],
    }
