"""
Funções puras de apresentação para a Similarity (Fase 4 do roadmap de
produto).

NÃO alteram nem recalculam nada de `similarity_engine.py` -- só
organizam o resultado já produzido por `find_similar_goalkeepers()` /
`explain_similarity()` para apresentação, sempre com o contexto
(competição/época/minutos) de cada candidato incluído. `similar`
(o DataFrame devolvido por `find_similar_goalkeepers`) não transporta
`competition_id`/`season_id` -- só `similarity_pct`, `similarity`,
`minutes` e as `STYLE_FEATURES` (ver `similarity_engine.build_scouting_...`
via `find_similar_goalkeepers`, que não é alterado aqui). Por isso o
contexto de cada candidato é lido de `table`, que já o tem.
"""

import pandas as pd


def reference_context(table: pd.DataFrame, target_player: str) -> pd.Series | None:
    """
    Contexto (competição/época/minutos, entre outras colunas) do jogador
    de referência, tal como usado por `find_similar_goalkeepers()` --
    que opera sempre sobre `table` (uma linha por jogador, a de mais
    minutos quando há várias). Devolve `None` se o jogador não estiver
    em `table` (tipicamente por não atingir os minutos mínimos da
    amostra).
    """
    if target_player not in table.index:
        return None
    return table.loc[target_player]


def build_similarity_rows(
    similar: pd.DataFrame,
    table: pd.DataFrame,
    target_player: str,
    market_lookup: dict,
    explain_fn,
    features,
) -> list[dict]:
    """
    Monta uma linha de apresentação por candidato de `similar` (o
    resultado de `find_similar_goalkeepers`, usado tal como veio, sem
    reordenar nem filtrar de novo).

    Cada linha inclui:

    - `similarity_pct`, exatamente como calculado;
    - contexto (`competition_id`, `season_id`, `minutes`), lido de
      `table` -- nunca inventado nem agregado entre candidatos;
    - dados de mercado, via `market_lookup` (o mapa já existente na
      app, não uma fonte de dados nova);
    - `explanation`, o resultado de `explain_fn` (normalmente
      `explain_similarity`) chamado sem alterações aos seus argumentos.

    A ordem dos resultados é a de `similar.index` -- não é reordenada
    aqui, por isso o ranking (`rank`) reflete exatamente o que
    `find_similar_goalkeepers` calculou.
    """

    rows = []

    for rank, candidate in enumerate(similar.index, start=1):

        context = table.loc[candidate] if candidate in table.index else None
        market = market_lookup.get(candidate)

        rows.append(
            {
                "rank": rank,
                "player_name": candidate,
                "similarity_pct": float(similar.loc[candidate, "similarity_pct"]),
                "competition_id": (
                    int(context["competition_id"]) if context is not None else None
                ),
                "season_id": (
                    int(context["season_id"]) if context is not None else None
                ),
                "minutes": (
                    float(context["minutes"]) if context is not None else None
                ),
                "current_club_name": (
                    None if market is None else market.get("current_club_name")
                ),
                "market_value_in_eur": (
                    None if market is None else market.get("market_value_in_eur")
                ),
                "explanation": explain_fn(
                    table,
                    target_player,
                    candidate,
                    features=features,
                ),
            }
        )

    return rows
