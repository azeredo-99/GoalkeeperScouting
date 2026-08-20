"""
Helpers de apresentação para o Player Profile -- puros, sem Streamlit.

Vivem fora de `streamlit_app.py` de propósito: esse script executa
código com efeitos secundários ao ser importado (liga-se à BD via
`load_data()`, chama a API do Streamlit), por isso não é seguro
importá-lo em testes. Estas funções não têm esse problema -- só
formatam ou selecionam valores já calculados; nunca recalculam uma
métrica nem tocam na base de dados.
"""

import pandas as pd

NO_ACTIONS_LABEL = "N/A — sem ações registadas"


def format_metric(value, fmt: str = "{:.1f}", suffix: str = "", empty: str = "N/A") -> str:
    """
    Formata um valor de métrica para apresentação.

    `NaN`/`None` NUNCA viram "0": ausência de dado é sempre apresentada
    como ausência (`empty`), nunca como um valor calculado. É o caso
    real de, por exemplo, `sweeper_actions` para um guarda-redes que
    nunca saiu da baliza (ver M5/S3).
    """
    if pd.isna(value):
        return empty
    return f"{fmt.format(value)}{suffix}"


def format_percentage(value, empty: str = "N/A") -> str:
    return format_metric(value, "{:.1f}", "%", empty)


def format_count(value, empty: str = "N/A") -> str:
    return format_metric(value, "{:.0f}", "", empty)


def format_rate_p90(value, empty: str = "N/A") -> str:
    return format_metric(value, "{:.2f}", "", empty)


def format_distance_m(value, empty: str = "N/A") -> str:
    return format_metric(value, "{:.1f}", " m", empty)


def context_label(row) -> str:
    """
    Rótulo legível de um contexto (competição/época/minutos).

    Usa os IDs em bruto -- `gk_performances` não tem nomes de competição
    (ver nota na Fase 2 sobre a tabela `competitions`, ainda por criar).
    """
    return (
        f"Competição #{int(row['competition_id'])} · "
        f"Época #{int(row['season_id'])} · "
        f"{row['minutes']:.0f} min"
    )


def player_context_rows(performances: pd.DataFrame, player_name: str | None) -> pd.DataFrame:
    """
    Devolve as linhas de `performances` para `player_name`, ordenadas
    pela amostra mais fiável primeiro (mais minutos).

    Não agrega nada: cada linha continua a ser um
    (player_name, competition_id, season_id) distinto -- é a base do
    seletor de contexto no Player Profile. Um `player_name` inexistente
    ou `None` devolve um DataFrame vazio (mesmas colunas), nunca lança
    exceção.
    """
    if performances.empty or player_name is None:
        return performances.iloc[0:0]

    rows = performances[performances["player_name"] == player_name]
    return rows.sort_values("minutes", ascending=False).reset_index(drop=True)
