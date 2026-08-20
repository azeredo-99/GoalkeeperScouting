"""
Pipeline de ingestão: build_scouting_table(context_columns=CONTEXT_COLUMNS)
-> registos upsertados em gk_performances.

Este módulo não recalcula nem reescreve nenhuma métrica -- chama
gk_scouting.metrics exatamente como já existe (ver `ingest()`). A única
responsabilidade daqui é transformar esse output no formato da tabela e
tratar da persistência (upsert idempotente).
"""

import math
from typing import Any

import pandas as pd
from sqlalchemy import Connection
from sqlalchemy.dialects.postgresql import insert as pg_insert

from gk_scouting.metrics import CONTEXT_COLUMNS, build_scouting_table

from .models import GKPerformance

# Mapeamento explícito pedido: "player" (nome do nível do índice que
# build_scouting_table produz) -> "player_name" (coluna da tabela). As
# restantes colunas (competition_id, season_id, e todas as métricas)
# já têm o mesmo nome dos dois lados, por isso não precisam de mapeamento.
_INDEX_RENAME = {"player": "player_name"}

# Todas as colunas que gk_performances exige, na ordem do modelo. Fonte
# única de verdade: GKPerformance (models.py) -- não uma lista duplicada
# à mão, para nunca divergir do schema real/da migration.
REQUIRED_COLUMNS = tuple(column.name for column in GKPerformance.__table__.columns)

_KEY_COLUMNS = ("player_name", "competition_id", "season_id")


class MissingColumnsError(RuntimeError):
    """
    Levantado quando o output de build_scouting_table já não contém
    alguma coluna que gk_performances precisa.

    É sempre um sinal de que metrics.py mudou de forma incompatível com o
    schema da BD -- corrigir aqui (por exemplo, inventando um valor por
    omissão) seria esconder o problema. Ou o schema evolui (nova
    migration) ou build_scouting_table volta a produzir a coluna.
    """


def table_to_records(table: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Converte o output de
    build_scouting_table(events, gk_events, gk_passes, context_columns=CONTEXT_COLUMNS)
    em registos prontos para upsert em gk_performances.

    Espera um índice MultiIndex (player, competition_id, season_id) --
    exatamente o que build_scouting_table devolve quando chamada com
    context_columns. Levanta ValueError com uma mensagem clara se o
    índice não tiver essa forma (por exemplo, se os eventos de origem não
    tinham colunas de contexto e build_scouting_table se degradou para o
    índice simples por jogador -- ver a docstring dessa função).
    """

    expected_index = ["player", *CONTEXT_COLUMNS]

    if list(table.index.names) != expected_index:
        raise ValueError(
            "build_scouting_table não devolveu o índice esperado "
            f"{expected_index}; recebido {list(table.index.names)}. "
            "Isto acontece quando os eventos de origem não têm colunas "
            "de contexto (competition_id/season_id) -- confirma que o "
            "dataset carregado é o multi-competição "
            "(data/events_extended.pkl), não events_full_wc2022.pkl."
        )

    frame = table.reset_index().rename(columns=_INDEX_RENAME)

    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise MissingColumnsError(
            f"build_scouting_table deixou de produzir a(s) coluna(s) {missing}, "
            "necessárias para gk_performances. O pipeline de ingestão parou "
            "em vez de gravar dados incompletos."
        )

    frame = frame[list(REQUIRED_COLUMNS)]

    return [
        {key: _to_sql_value(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def _to_sql_value(value: Any) -> Any:
    """
    Normaliza um valor de célula pandas/numpy para um tipo nativo Python.

    NaN passa a None (NULL SQL), nunca fica como o valor especial de
    ponto flutuante NaN -- "sem dados" (ex.: guarda-redes que nunca saiu
    da baliza, ver M5/S3) e "not-a-number" não são a mesma coisa, e um
    FLOAT NaN gravado na BD seria lido de volta como um valor presente,
    não como ausência de dado.
    """

    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    if hasattr(value, "item"):  # escalar numpy (int64, float64, ...)
        value = value.item()
        if isinstance(value, float) and math.isnan(value):
            return None

    return value


def build_upsert_statement(records: list[dict[str, Any]]):
    """
    Constrói (sem executar) a instrução de upsert para `records`.

    Usa INSERT ... ON CONFLICT (player_name, competition_id, season_id)
    DO UPDATE -- a chave única da tabela (constraint pk_gk_performances)
    -- para que correr o pipeline outra vez atualize as linhas existentes
    em vez de as duplicar. É esta construção SQL, não qualquer lógica em
    Python, que garante a idempotência.
    """

    if not records:
        raise ValueError("Nenhum registo para upsert (records está vazio).")

    stmt = pg_insert(GKPerformance).values(records)

    update_columns = {
        column: getattr(stmt.excluded, column)
        for column in REQUIRED_COLUMNS
        if column not in _KEY_COLUMNS
    }

    return stmt.on_conflict_do_update(
        constraint="pk_gk_performances",
        set_=update_columns,
    )


def ingest(
    events: pd.DataFrame,
    gk_events: pd.DataFrame,
    gk_passes: pd.DataFrame,
    connection: Connection,
) -> int:
    """
    Corre o pipeline completo: métricas -> transformação -> upsert.

    Reutiliza build_scouting_table sem alterações -- a única lógica de
    scouting aqui é a chamada em si. `connection` é uma ligação
    SQLAlchemy já aberta; o ciclo de vida da transação (commit/rollback)
    é responsabilidade de quem chama (ver ingest_performances.py).

    Devolve o número de registos upsertados.
    """

    table = build_scouting_table(
        events,
        gk_events,
        gk_passes,
        context_columns=CONTEXT_COLUMNS,
    )

    records = table_to_records(table)
    statement = build_upsert_statement(records)

    connection.execute(statement)

    return len(records)
