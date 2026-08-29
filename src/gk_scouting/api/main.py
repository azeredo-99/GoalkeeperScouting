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
from statsbombpy import sb

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
from gk_scouting.benchmarking import DEFAULT_MIN_MINUTES, build_benchmark
from gk_scouting.comparison import build_comparison_table
from gk_scouting.data_coverage import build_coverage
from gk_scouting.presentation import player_context_rows
from gk_scouting.scouting_profiles import (
    DEFAULT_PROFILES,
    PREFERENCE_METRICS,
    ScoutingProfile,
    get_profile,
    parse_custom_profile,
)
from gk_scouting.scouting_match import ScoutingMatchResult, match_player_to_profile
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


@lru_cache(maxsize=1)
def _competition_names() -> dict:
    """
    (competition_id, season_id) -> (competition_name, season_name), a
    partir da mesma fonte real que download_extended_data.py já usa
    (StatsBomb open-data). Nunca inventa nomes -- se a chamada de rede
    falhar, devolve um dicionário vazio e o chamador usa um rótulo
    neutro em vez de mostrar o id interno ao utilizador.
    """
    try:
        competitions = sb.competitions()
    except Exception:
        return {}

    lookup = {}
    for _, row in competitions.iterrows():
        key = (int(row["competition_id"]), int(row["season_id"]))
        lookup[key] = (row["competition_name"], row["season_name"])
    return lookup


def _context_names(competition_id: int, season_id: int) -> tuple:
    names = _competition_names().get((competition_id, season_id))
    if names is None:
        return ("Unnamed competition", "Unnamed season")
    return names


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


def _metrics_dict(row: pd.Series) -> dict:
    """
    As mesmas três categorias já usadas em todo o produto (Shot
    Stopping/Sweeping/Distribution), a partir das colunas que já existem
    em `row` -- nenhum cálculo novo. Extraído de `_row_to_dict` para ser
    reutilizado também pela Similarity (Fase Scouting Intelligence), que
    precisa dos mesmos valores brutos para agrupar a explicação por
    dimensão sem inventar um sub-score.
    """
    return {
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
    }


def _match_input(row: pd.Series, market_lookup: dict) -> dict:
    """
    O dict que `scouting_match.match_player_to_profile` espera --
    exatamente as colunas já calculadas por metrics.py mais idade/valor
    de mercado do mapa de mercado já existente. Nenhum valor novo,
    nenhum recálculo.
    """
    market = market_lookup.get(row["player_name"] if "player_name" in row else row.name)
    return {
        "save_pct": _clean(row.get("save_pct")),
        "sweeper_actions_p90": _clean(row.get("sweeper_actions_p90")),
        "avg_distance_from_goal": _clean(row.get("avg_distance_from_goal")),
        "pass_success_pct": _clean(row.get("pass_success_pct")),
        "long_ball_pct": _clean(row.get("long_ball_pct")),
        "age": calculate_age(market.get("date_of_birth")) if market is not None else None,
        "market_value_eur": _clean(market.get("market_value_in_eur")) if market is not None else None,
        "minutes": _clean(row.get("minutes")),
    }


def _profile_dict(profile: ScoutingProfile) -> dict:
    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "preferences": [
            {
                "metric": pref.metric,
                "label": PREFERENCE_METRICS[pref.metric],
                "enabled": pref.enabled,
                "weight": pref.weight,
                "minimum": pref.minimum,
                "maximum": pref.maximum,
            }
            for pref in profile.preferences.values()
        ],
    }


def _match_result_dict(result: ScoutingMatchResult) -> dict:
    return {
        "profileId": result.profile_id,
        "profileName": result.profile_name,
        "matchedCount": result.matched_count,
        "unmetCount": result.unmet_count,
        "insufficientCount": result.insufficient_count,
        "matchScore": result.match_score,
        "evaluations": [
            {
                "metric": e.metric,
                "label": e.label,
                "status": e.status,
                "value": _clean(e.value),
                "minimum": e.minimum,
                "maximum": e.maximum,
                "weight": e.weight,
            }
            for e in result.evaluations
        ],
    }


def _row_to_dict(row: pd.Series, market_lookup: dict) -> dict:
    market = market_lookup.get(row["player_name"] if "player_name" in row else row.name)
    competition_id = int(row["competition_id"])
    season_id = int(row["season_id"])
    competition_name, season_name = _context_names(competition_id, season_id)
    return {
        "playerName": row.get("player_name", row.name),
        "competitionId": competition_id,
        "seasonId": season_id,
        "competitionName": competition_name,
        "seasonName": season_name,
        "minutes": _clean(row["minutes"]),
        "club": _clean(market.get("current_club_name")) if market is not None else None,
        "age": calculate_age(market.get("date_of_birth")) if market is not None else None,
        "marketValueEur": _clean(market.get("market_value_in_eur")) if market is not None else None,
        "metrics": _metrics_dict(row),
    }


# ---------------------------------------------------------------------------
# Competitions / Seasons
# ---------------------------------------------------------------------------

@app.get("/api/competitions")
def get_competitions():
    """Competições realmente presentes nos dados, com nome real (nunca o id)."""
    performances, _, _ = _state()
    names_by_competition: dict[int, str] = {}
    for (competition_id, _season_id), (competition_name, _season_name) in _competition_names().items():
        names_by_competition.setdefault(competition_id, competition_name)

    return {
        "competitions": [
            {"id": cid, "name": names_by_competition.get(cid, "Unnamed competition")}
            for cid in available_competitions(performances)
        ]
    }


@app.get("/api/seasons")
def get_seasons(competition_id: int | None = None):
    """Épocas realmente presentes (restritas à competição, se indicada), com nome real."""
    performances, _, _ = _state()
    season_ids = available_seasons(performances, competition_id)

    seasons = []
    for season_id in season_ids:
        if competition_id is not None:
            _, season_name = _context_names(competition_id, season_id)
        else:
            season_name = next(
                (name for (_cid, sid), (_cname, name) in _competition_names().items() if sid == season_id),
                "Unnamed season",
            )
        seasons.append({"id": season_id, "name": season_name})

    return {"seasons": seasons}


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
    min_save_pct: float | None = None,
    min_sweeper_actions_p90: float | None = None,
    min_pass_success_pct: float | None = None,
    min_long_ball_pct: float | None = None,
    scouting_profile_id: str | None = None,
    custom_profile: str | None = None,
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
        min_save_pct=min_save_pct,
        min_sweeper_actions_p90=min_sweeper_actions_p90,
        min_pass_success_pct=min_pass_success_pct,
        min_long_ball_pct=min_long_ball_pct,
    )

    # Scouting Match é opt-in e nunca substitui os resultados nem a
    # ordenação por omissão -- só anexa `scoutingMatch` a cada linha
    # quando um perfil válido é pedido explicitamente. `custom_profile`
    # (definição inline enviada pelo frontend a partir do localStorage do
    # scout -- ver customScoutingProfiles.ts) tem prioridade sobre
    # `scouting_profile_id` quando ambos chegam. Um perfil inválido ou
    # desconhecido é sempre um erro explícito (400/404) -- nunca um
    # resultado sem perfil aplicado a passar por "nenhum perfil pedido".
    if custom_profile:
        try:
            profile = parse_custom_profile(custom_profile)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    elif scouting_profile_id:
        profile = get_profile(scouting_profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"Unknown scouting profile: '{scouting_profile_id}'")
    else:
        profile = None

    results = []
    for _, row in candidates.iterrows():
        result = _row_to_dict(row, market_lookup)
        if profile is not None:
            match = match_player_to_profile(_match_input(row, market_lookup), profile)
            result["scoutingMatch"] = _match_result_dict(match)
        results.append(result)

    return {"results": results}


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
# Benchmark
# ---------------------------------------------------------------------------

@app.get("/api/players/{player_name}/benchmark")
def get_player_benchmark(
    player_name: str,
    competition_id: int,
    season_id: int,
    min_minutes: float = DEFAULT_MIN_MINUTES,
):
    performances, _, _ = _state()
    result = build_benchmark(performances, player_name, competition_id, season_id, min_minutes)
    competition_name, season_name = _context_names(competition_id, season_id)

    return {
        "competitionName": competition_name,
        "seasonName": season_name,
        "minimumMinutes": result["minimumMinutes"],
        "totalPeerCount": result["totalPeerCount"],
        "available": result["available"],
        "metrics": [
            {
                "key": m["key"],
                "label": m["label"],
                "category": m["category"],
                "value": _clean(m["value"]),
                "percentile": _clean(m["percentile"]),
                "peerCount": m["peerCount"],
                "status": m["status"],
            }
            for m in result["metrics"]
        ],
    }


# ---------------------------------------------------------------------------
# Scouting Profiles / Scouting Match
# ---------------------------------------------------------------------------

@app.get("/api/scouting-profiles")
def list_scouting_profiles():
    """Perfis de scouting predefinidos -- predefinições do scout, não classificações objetivas."""
    return {"profiles": [_profile_dict(p) for p in DEFAULT_PROFILES]}


@app.get("/api/scouting-profiles/{profile_id}")
def get_scouting_profile(profile_id: str):
    profile = get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Scouting profile not found")
    return _profile_dict(profile)


@app.get("/api/players/{player_name}/scouting-match")
def get_scouting_match(player_name: str, profile_id: str, competition_id: int, season_id: int):
    """
    PLAYER × PROFILE × CONTEXT -- nunca um valor armazenado ou
    independente de perfil/contexto. Reavaliado a cada pedido a partir
    dos dados já existentes.
    """
    performances, _, market_lookup = _state()

    profile = get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Scouting profile not found")

    match = performances[
        (performances["player_name"] == player_name)
        & (performances["competition_id"] == competition_id)
        & (performances["season_id"] == season_id)
    ]
    if match.empty:
        raise HTTPException(status_code=404, detail="No performance for this player in this context")

    result = match_player_to_profile(_match_input(match.iloc[0], market_lookup), profile)
    return _match_result_dict(result)


# ---------------------------------------------------------------------------
# Data Coverage (internal)
# ---------------------------------------------------------------------------

@app.get("/api/data-coverage")
def get_data_coverage():
    """
    Visão interna de cobertura por competição/época -- nunca um número
    inventado, só o que já está em `gk_performances`.
    """
    performances, _, _ = _state()
    rows = build_coverage(performances)

    contexts = []
    for r in rows:
        competition_name, season_name = _context_names(r["competition_id"], r["season_id"])
        contexts.append(
            {
                "competitionId": r["competition_id"],
                "seasonId": r["season_id"],
                "competitionName": competition_name,
                "seasonName": season_name,
                "totalGoalkeepers": r["total_goalkeepers"],
                "benchmarkableGoalkeepers": r["benchmarkable_goalkeepers"],
                "status": r["status"],
            }
        )

    return {"minimumMinutes": DEFAULT_MIN_MINUTES, "contexts": contexts}


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

    target_competition_id = int(context["competition_id"])
    target_season_id = int(context["season_id"])
    target_competition_name, target_season_name = _context_names(target_competition_id, target_season_id)

    def _result_dict(r):
        competition_id = int(r["competition_id"])
        season_id = int(r["season_id"])
        competition_name, season_name = _context_names(competition_id, season_id)
        # `r["player_name"]` está garantidamente em `table` -- é um dos
        # candidatos devolvidos por `find_similar_goalkeepers`, que só
        # opera sobre linhas já presentes em `table`. Os valores brutos
        # (save_pct, sweeper_actions_p90, ...) são exatamente os que o
        # algoritmo usou -- só reaproveitados para apresentação, nunca
        # recalculados.
        candidate_metrics = _metrics_dict(table.loc[r["player_name"]])
        return {
            "rank": r["rank"],
            "playerName": r["player_name"],
            "competitionId": competition_id,
            "seasonId": season_id,
            "competitionName": competition_name,
            "seasonName": season_name,
            "minutes": _clean(r["minutes"]),
            "club": r["current_club_name"],
            "marketValueEur": _clean(r["market_value_in_eur"]),
            "similarityPct": round(r["similarity_pct"], 1),
            "explanation": r["explanation"],
            "metrics": candidate_metrics,
        }

    return {
        "target": _identity(target, market_lookup) | {
            "competitionId": target_competition_id,
            "seasonId": target_season_id,
            "competitionName": target_competition_name,
            "seasonName": target_season_name,
            "minutes": _clean(context["minutes"]),
            "metrics": _metrics_dict(context),
        },
        "results": [_result_dict(r) for r in rows],
    }
