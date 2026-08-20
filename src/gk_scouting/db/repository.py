"""
Camada de leitura (repository) para `gk_performances`.

Não calcula nenhuma métrica -- lê o que já está materializado na BD (ver
`gk_scouting.db.ingest`, que grava lá o output de
`build_scouting_table()`). `build_scouting_table()` continua a ser a
única fonte de cálculo das métricas, mas só dentro do pipeline de
ingestão; este módulo só sabe ler o resultado já persistido.
"""

import pandas as pd
from sqlalchemy import Engine, create_engine, select

from .config import get_database_url
from .models import GKPerformance

# Colunas devolvidas, na mesma ordem do modelo: identidade
# (player_name, competition_id, season_id) + todas as métricas.
COLUMNS = tuple(column.name for column in GKPerformance.__table__.columns)


def load_gk_performances(engine: Engine | None = None) -> pd.DataFrame:
    """
    Lê todas as linhas de `gk_performances` e devolve um DataFrame plano.

    Uma linha = um (player_name, competition_id, season_id), exatamente
    como gravado pelo pipeline de ingestão -- sem agregação, sem
    recálculo, sem índice especial. Um jogador com performances em mais
    do que uma competição/época aparece em várias linhas; é quem chama
    que decide como as colapsar, se precisar (ver `streamlit_app.py`).

    Se `engine` não for passado, cria-se um a partir de `DATABASE_URL`
    (ver `gk_scouting.db.config.get_database_url` -- levanta
    `RuntimeError` com mensagem clara se a variável não estiver
    definida). Passar um `engine` próprio serve sobretudo para testes.

    Sem linhas na tabela, devolve um DataFrame vazio mas com as colunas
    corretas (nunca um DataFrame sem colunas nenhumas) -- para que o
    código que consome o resultado não precise de casos especiais.
    """

    owns_engine = engine is None
    if owns_engine:
        engine = create_engine(get_database_url())

    try:
        with engine.connect() as connection:
            rows = connection.execute(select(GKPerformance)).mappings().all()
    finally:
        if owns_engine:
            engine.dispose()

    if not rows:
        return pd.DataFrame(columns=list(COLUMNS))

    return pd.DataFrame(rows, columns=list(COLUMNS))
