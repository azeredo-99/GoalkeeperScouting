"""
gk_scouting
-----------

Biblioteca de scouting de guarda-redes a partir de dados StatsBomb Open Data
e de contexto de mercado do Transfermarkt.

Os módulos estão organizados por responsabilidade:

    data_loader       ingestão de eventos StatsBomb
    metrics           agregação de eventos em métricas por guarda-redes
    similarity_engine comparação de perfis e pesquisa de semelhantes
    market_data       carregamento da base de valores de mercado
    player_matching   ligação entre nomes StatsBomb e Transfermarkt
    visuals           radar comparativo e mapa de saídas
    readable_report   relatórios em texto para leitura humana

Os pontos de entrada (`main.py`, `streamlit_app.py`,
`download_extended_data.py`) vivem na raiz do repositório e consomem
este pacote.
"""

__all__ = [
    "data_loader",
    "market_data",
    "metrics",
    "player_matching",
    "readable_report",
    "similarity_engine",
    "visuals",
]
