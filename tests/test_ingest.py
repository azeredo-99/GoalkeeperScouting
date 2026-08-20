"""
Testes do pipeline de ingestão (build_scouting_table -> gk_performances).

Sem PostgreSQL disponível nesta fase (validação pendente, registada e
aceite), estes testes cobrem apenas o que é verificável sem ligação real:

* a transformação do output de build_scouting_table para o formato de
  gk_performances (table_to_records);
* que a instrução de upsert gerada (build_upsert_statement) é, de facto,
  um INSERT ... ON CONFLICT DO UPDATE correto -- a garantia de
  idempotência vem desta construção SQL, não de a termos corrido contra
  uma base de dados real;
* que build_scouting_table deixar de produzir uma coluna esperada é
  detetado e para o pipeline, em vez de gravar dados incompletos.

NÃO testa execução real contra Postgres -- isso fica como validação
pendente, não fingido aqui.
"""

import numpy as np
import pandas as pd
import pytest
from sqlalchemy.dialects import postgresql

from conftest import EVENT_COLUMNS, filler, gk_event, starting_xi
from gk_scouting.data_loader import build_gk_events, build_gk_passes
from gk_scouting.db.ingest import (
    MissingColumnsError,
    REQUIRED_COLUMNS,
    _to_sql_value,
    build_upsert_statement,
    table_to_records,
)
from gk_scouting.db.models import GKPerformance
from gk_scouting.metrics import CONTEXT_COLUMNS, build_scouting_table


# ---------------------------------------------------------------------------
# Dataset sintético com duas competições/épocas (isolado deste ficheiro;
# não reutiliza os helpers de test_context.py de propósito, para manter
# esta alteração pequena e sem dependências cruzadas entre testes).
# ---------------------------------------------------------------------------

def _tag(row, competition_id, season_id):
    row = dict(row)
    row["competition_id"] = competition_id
    row["season_id"] = season_id
    return row


def _events_with_two_contexts():
    """
    Um único guarda-redes, dois jogos em competições/épocas diferentes.
    Suficiente para produzir um índice MultiIndex real de duas linhas.
    """
    columns = [*EVENT_COLUMNS, "competition_id", "season_id"]

    rows = [
        _tag(starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]), 1, 2022),
        _tag(gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"), 1, 2022),
        _tag(gk_event(1, 1, 20, "Keeper", "Team X", "Goal Conceded"), 1, 2022),
        _tag(filler(1, 2, 90), 1, 2022),
        _tag(starting_xi(2, "Team X", [("Keeper", "Goalkeeper")]), 2, 2023),
        _tag(gk_event(2, 1, 10, "Keeper", "Team X", "Shot Saved"), 2, 2023),
        _tag(filler(2, 2, 90), 2, 2023),
    ]
    return pd.DataFrame(rows, columns=columns)


def _real_table():
    """
    A tabela real produzida por build_scouting_table, sem qualquer
    alteração à função -- é isto que table_to_records recebe em produção.
    """
    events = _events_with_two_contexts()
    return build_scouting_table(
        events,
        build_gk_events(events),
        build_gk_passes(events),
        context_columns=CONTEXT_COLUMNS,
    )


# ===========================================================================
# table_to_records -- transformação
# ===========================================================================

def test_records_are_produced_for_each_context_row():
    table = _real_table()
    records = table_to_records(table)
    assert len(records) == len(table) == 2


def test_index_level_player_is_renamed_to_player_name():
    records = table_to_records(_real_table())
    assert all("player_name" in record for record in records)
    assert all("player" not in record for record in records)
    assert {r["player_name"] for r in records} == {"Keeper"}


def test_competition_and_season_columns_are_preserved_verbatim():
    records = table_to_records(_real_table())
    combos = {(r["competition_id"], r["season_id"]) for r in records}
    assert combos == {(1, 2022), (2, 2023)}


def test_every_record_has_exactly_the_required_columns():
    records = table_to_records(_real_table())
    for record in records:
        assert set(record.keys()) == set(REQUIRED_COLUMNS)


def test_nan_metrics_become_none_not_float_nan():
    """
    Um guarda-redes que nunca saiu da baliza tem sweeper_actions = NaN em
    pandas (ver M5/S3, ainda não resolvido no domínio). Aqui tem de virar
    None (NULL SQL) -- gravar o valor especial de ponto flutuante NaN
    seria armazenar "não é um número" onde o correto é "sem dado".
    """
    records = table_to_records(_real_table())
    # Nenhuma das duas linhas tem eventos "Keeper Sweeper" neste cenário.
    for record in records:
        assert record["sweeper_actions"] is None
        assert not isinstance(record["sweeper_actions"], float)


def test_numeric_values_are_native_python_types_not_numpy():
    record = table_to_records(_real_table())[0]
    assert type(record["minutes"]) is float
    assert type(record["competition_id"]) is int


def test_missing_index_shape_raises_a_clear_error():
    """
    Se build_scouting_table se degradar para o índice simples por
    jogador (dataset sem colunas de contexto), a transformação tem de
    parar de forma explícita, não inventar competition_id/season_id.
    """
    table = pd.DataFrame(
        {"minutes": [90.0]},
        index=pd.Index(["Keeper"], name="player"),
    )
    with pytest.raises(ValueError, match="índice esperado"):
        table_to_records(table)


def test_missing_required_column_raises_missing_columns_error():
    """
    Este é o requisito 5: se build_scouting_table deixar de produzir uma
    coluna que gk_performances exige, o pipeline falha alto, em vez de
    gravar uma linha incompleta.
    """
    table = _real_table().drop(columns=["save_pct"])
    with pytest.raises(MissingColumnsError, match="save_pct"):
        table_to_records(table)


def test_multiple_missing_columns_are_all_named_in_the_error():
    table = _real_table().drop(columns=["save_pct", "total_passes"])
    with pytest.raises(MissingColumnsError) as excinfo:
        table_to_records(table)
    assert "save_pct" in str(excinfo.value)
    assert "total_passes" in str(excinfo.value)


def test_required_columns_are_derived_from_the_real_model():
    """
    REQUIRED_COLUMNS não é uma lista solta escrita à mão -- vem
    diretamente de GKPerformance, para nunca divergir do schema real
    nem da migration.
    """
    model_columns = tuple(column.name for column in GKPerformance.__table__.columns)
    assert REQUIRED_COLUMNS == model_columns


# ===========================================================================
# _to_sql_value
# ===========================================================================

def test_to_sql_value_converts_nan_to_none():
    assert _to_sql_value(float("nan")) is None


def test_to_sql_value_passes_none_through():
    assert _to_sql_value(None) is None


def test_to_sql_value_converts_numpy_scalars_to_native_python():
    assert _to_sql_value(np.float64(3.5)) == 3.5
    assert type(_to_sql_value(np.float64(3.5))) is float
    assert _to_sql_value(np.int64(7)) == 7
    assert type(_to_sql_value(np.int64(7))) is int


def test_to_sql_value_converts_numpy_nan_to_none():
    assert _to_sql_value(np.float64("nan")) is None


def test_to_sql_value_keeps_strings_unchanged():
    assert _to_sql_value("Keeper") == "Keeper"


# ===========================================================================
# build_upsert_statement -- validado por compilação, não execução
# ===========================================================================

def _compiled_sql(statement):
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def test_upsert_statement_is_an_insert_into_gk_performances():
    records = table_to_records(_real_table())
    sql = _compiled_sql(build_upsert_statement(records))
    assert sql.startswith("INSERT INTO gk_performances")
    assert sql.count("INSERT INTO gk_performances") == 1


def test_upsert_statement_targets_the_primary_key_constraint():
    records = table_to_records(_real_table())
    sql = _compiled_sql(build_upsert_statement(records))
    assert "ON CONFLICT ON CONSTRAINT pk_gk_performances" in sql
    assert "DO UPDATE SET" in sql


def test_upsert_statement_updates_every_metric_column_except_the_key():
    records = table_to_records(_real_table())
    sql = _compiled_sql(build_upsert_statement(records))
    for column in REQUIRED_COLUMNS:
        if column in ("player_name", "competition_id", "season_id"):
            continue
        assert f"{column} = excluded.{column}" in sql


def test_upsert_statement_does_not_reassign_the_key_columns():
    """
    A chave (player_name, competition_id, season_id) define o conflito;
    não deve aparecer também no SET -- seria redundante e, em teoria,
    permitiria "mover" uma linha para outra chave via upsert.
    """
    records = table_to_records(_real_table())
    sql = _compiled_sql(build_upsert_statement(records))
    assert "player_name = excluded.player_name" not in sql
    assert "competition_id = excluded.competition_id" not in sql
    assert "season_id = excluded.season_id" not in sql


def test_upsert_statement_contains_a_row_per_record():
    records = table_to_records(_real_table())
    sql = _compiled_sql(build_upsert_statement(records))
    assert sql.count("'Keeper'") == len(records)


def test_empty_records_raises_instead_of_building_an_empty_statement():
    with pytest.raises(ValueError, match="Nenhum registo"):
        build_upsert_statement([])


# ===========================================================================
# Idempotência -- a parte demonstrável sem uma BD real
# ===========================================================================
#
# A não-duplicação depende de duas coisas: (1) a transformação ser
# determinística, testado abaixo; (2) o ON CONFLICT DO UPDATE do upsert,
# testado acima por compilação da instrução. As duas juntas garantem que
# correr o pipeline duas vezes sobre os mesmos dados de origem ATUALIZA
# as mesmas linhas em vez de as duplicar -- mas isso só fica provado de
# facto contra Postgres real (ver validação pendente).

def test_transforming_the_same_table_twice_produces_identical_records():
    table = _real_table()
    assert table_to_records(table) == table_to_records(table)


def test_two_runs_target_the_same_conflict_keys():
    table = _real_table()

    def keys():
        return {
            (r["player_name"], r["competition_id"], r["season_id"])
            for r in table_to_records(table)
        }

    assert keys() == keys()


def test_rerunning_the_full_pipeline_on_unchanged_data_yields_the_same_statement_sql():
    """
    Se os dados de origem não mudam, o SQL do upsert gerado numa segunda
    execução tem de ser byte-a-byte igual ao da primeira -- não há
    nenhuma fonte de não-determinismo (ordem de linhas, ids gerados) que
    pudesse levar a duplicação silenciosa.
    """
    table = _real_table()
    sql_first = _compiled_sql(build_upsert_statement(table_to_records(table)))
    sql_second = _compiled_sql(build_upsert_statement(table_to_records(table)))
    assert sql_first == sql_second
