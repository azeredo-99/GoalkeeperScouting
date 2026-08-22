"""
Funções puras para o Performance Benchmark do Player Profile (v1).

Responde a uma pergunta contextual: "como é que este guarda-redes se
compara aos pares dele nesta competição/época?" -- nunca uma pergunta
global ("é bom guarda-redes?"). Por isso o peer group é sempre
competition + season + minimum minutes, nunca uma população universal.

Vive fora de `streamlit_app.py`/`api/main.py` pela mesma razão que
`discovery.py`/`comparison.py`/`similarity_view.py`: é pura, testável
sem BD nem FastAPI. Não recalcula nenhuma métrica -- lê exclusivamente
colunas já produzidas por `metrics.py`.
"""

import pandas as pd

# (key, coluna em gk_performances, label legível, categoria do Player
# Profile) -- só as 5 métricas validadas na análise de viabilidade.
BENCHMARK_METRICS = [
    ("save_pct", "save_pct", "Save %", "Shot Stopping"),
    ("sweeper_actions_p90", "sweeper_actions_p90", "Actions /90", "Sweeping"),
    ("avg_distance_from_goal", "avg_distance_from_goal", "Avg. distance", "Sweeping"),
    ("pass_success_pct", "pass_success_pct", "Pass success", "Distribution"),
    ("long_ball_pct", "long_ball_pct", "Long ball %", "Distribution"),
]

DEFAULT_MIN_MINUTES = 450.0


def peer_pool(
    performances: pd.DataFrame,
    player_name: str,
    competition_id: int,
    season_id: int,
    min_minutes: float = DEFAULT_MIN_MINUTES,
) -> pd.DataFrame:
    """
    Outros guarda-redes na mesma competition/season com minutes >=
    min_minutes -- nunca o próprio jogador (não faz sentido comparar
    alguém contra si próprio).
    """
    return performances[
        (performances["competition_id"] == competition_id)
        & (performances["season_id"] == season_id)
        & (performances["minutes"] >= min_minutes)
        & (performances["player_name"] != player_name)
    ]


def percentile_rank(value: float, peer_values: list) -> float:
    """
    Percentile rank determinístico dentro do peer group, com average-rank
    tie handling -- sem depender de numpy/scipy.

        percentile = (peers_abaixo + 0.5 * peers_empatados) / n_peers * 100

    Um jogador estritamente acima de todos os pares fica perto de 100;
    estritamente abaixo de todos fica perto de 0; empates partilham o
    percentile médio da posição em vez de desempate arbitrário. Não
    implica "melhor" nem "pior" -- é só a posição do valor entre pares,
    a leitura fica com o scout.
    """
    n = len(peer_values)
    if n == 0:
        return None
    below = sum(1 for v in peer_values if v < value)
    tied = sum(1 for v in peer_values if v == value)
    return (below + 0.5 * tied) / n * 100.0


def _tier(peer_count: int) -> str:
    if peer_count < 5:
        return "insufficient"
    if peer_count < 10:
        return "small"
    return "normal"


def build_benchmark(
    performances: pd.DataFrame,
    player_name: str,
    competition_id: int,
    season_id: int,
    min_minutes: float = DEFAULT_MIN_MINUTES,
) -> dict:
    """
    Monta o benchmark contextual de um jogador para uma competition/season
    específica. Não resolve nomes de competição/época (isso é
    responsabilidade da camada API, que já tem esse cache).

    `available` reflete o peer pool de contexto (independente de métrica)
    -- usado pelo frontend para decidir entre mostrar a secção ou o empty
    state "Benchmark unavailable for this sample.". Cada métrica tem o
    seu próprio `peerCount`/`status`, porque métricas como sweeping têm
    missing values reais que reduzem o número de pares comparáveis nessa
    métrica especificamente, mesmo quando o contexto no geral tem pares
    suficientes.
    """
    pool = peer_pool(performances, player_name, competition_id, season_id, min_minutes)
    total_peer_count = len(pool)

    target_rows = performances[
        (performances["player_name"] == player_name)
        & (performances["competition_id"] == competition_id)
        & (performances["season_id"] == season_id)
    ]
    target_row = target_rows.iloc[0] if not target_rows.empty else None

    metrics_out = []
    for key, column, label, category in BENCHMARK_METRICS:
        player_value = None
        if target_row is not None:
            raw = target_row.get(column)
            if raw is not None and not pd.isna(raw):
                player_value = float(raw)

        peer_values = [float(v) for v in pool[column].dropna().tolist()]
        peer_count = len(peer_values)

        if player_value is None:
            status = "no_data"
            percentile = None
        elif peer_count < 5:
            status = "insufficient"
            percentile = None
        else:
            status = _tier(peer_count)
            percentile = percentile_rank(player_value, peer_values)

        metrics_out.append(
            {
                "key": key,
                "label": label,
                "category": category,
                "value": player_value,
                "percentile": percentile,
                "peerCount": peer_count,
                "status": status,
            }
        )

    return {
        "minimumMinutes": min_minutes,
        "totalPeerCount": total_peer_count,
        "available": total_peer_count >= 5,
        "metrics": metrics_out,
    }
