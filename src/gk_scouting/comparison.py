"""
Funções puras para a página de Comparação (Fase 4 do roadmap de
produto).

Cada jogador na comparação mantém o seu próprio contexto
(competition_id, season_id) -- nunca a linha agregada de mais minutos
usada como fallback noutras páginas. Vivem fora de `streamlit_app.py`
pela mesma razão que `presentation.py`/`discovery.py`: são testáveis
sem Streamlit nem BD.
"""

import pandas as pd


def build_comparison_table(rows) -> pd.DataFrame:
    """
    Junta as linhas de contexto escolhidas (uma por jogador, cada uma já
    a linha específica de `(player_name, competition_id, season_id)`
    selecionada para esse jogador) numa única tabela indexada por
    `player_name` -- o formato que `plot_radar()` e a tabela de métricas
    da comparação já esperam.

    `rows` é um iterável de `pd.Series` (uma por jogador, tipicamente
    vinda de `player_context_rows`). Não recalcula nem agrega nada: é só
    a montagem das linhas já escolhidas. Entradas `None` são ignoradas
    (jogador sem linha correspondente).
    """
    valid_rows = [row for row in rows if row is not None]

    if not valid_rows:
        return pd.DataFrame()

    table = pd.DataFrame(valid_rows).set_index("player_name")
    table.index.name = "player"
    return table
