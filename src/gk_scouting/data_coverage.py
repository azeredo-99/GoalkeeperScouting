"""
Data Coverage -- visão interna/administrativa de quanto o sistema
"sabe" por competição/época, a partir exclusivamente dos dados já em
`gk_performances`. Não é uma página voltada para o utilizador final,
não inventa nenhum número: cada contagem vem diretamente do DataFrame
já carregado (a mesma fonte que `discovery.py`/`benchmarking.py` usam).

Os limiares de status reutilizam exatamente os mesmos cortes já
validados em `benchmarking._tier` (5 e 10 pares comparáveis) -- não são
uma escala nova inventada para esta página.
"""

import pandas as pd

from .benchmarking import DEFAULT_MIN_MINUTES


def _status(benchmarkable: int) -> str:
    if benchmarkable == 0:
        return "insufficient"
    if benchmarkable < 5:
        return "limited"
    if benchmarkable < 10:
        return "partial"
    return "strong"


def build_coverage(performances: pd.DataFrame, min_minutes: float = DEFAULT_MIN_MINUTES) -> list[dict]:
    """
    Uma linha por (competition_id, season_id) realmente presente nos
    dados: total de guarda-redes com performance nesse contexto, e
    quantos atingem `min_minutes` (o mesmo limiar usado pelo Benchmark)
    -- ou seja, quantos formariam um peer pool utilizável.
    """
    if performances.empty:
        return []

    rows = []
    grouped = performances.groupby(["competition_id", "season_id"])
    for (competition_id, season_id), group in grouped:
        benchmarkable = int((group["minutes"] >= min_minutes).sum())
        rows.append(
            {
                "competition_id": int(competition_id),
                "season_id": int(season_id),
                "total_goalkeepers": int(len(group)),
                "benchmarkable_goalkeepers": benchmarkable,
                "status": _status(benchmarkable),
            }
        )

    return sorted(rows, key=lambda r: r["benchmarkable_goalkeepers"], reverse=True)
