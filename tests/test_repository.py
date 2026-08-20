"""
Testes de `load_gk_performances` (camada de leitura de `gk_performances`).

Sem PostgreSQL disponível nesta fase, estes testes usam SQLite em
memória via SQLAlchemy: o caminho testado (`select(GKPerformance)` +
conversão `RowMapping` -> `DataFrame`) não depende de sintaxe específica
de dialecto -- ao contrário do upsert em `ingest.py` (que usa
`ON CONFLICT`, exclusivo de Postgres, e não é tocado aqui), um `SELECT`
simples corre de forma idêntica em qualquer motor SQL. Isto valida a
transformação SQLAlchemy -> DataFrame de forma honesta, mas NÃO prova
que a ligação a um Postgres real funciona -- isso fica registado como
validação pendente.
"""

import pandas as pd
import pytest
from sqlalchemy import create_engine

from gk_scouting.db.models import Base, GKPerformance
from gk_scouting.db.repository import COLUMNS, load_gk_performances


@pytest.fixture
def sqlite_engine():
    """Motor SQLite em memória com o schema de gk_performances criado."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def _row(player_name, competition_id, season_id, minutes, **overrides):
    row = {column: None for column in COLUMNS}
    row.update(
        player_name=player_name,
        competition_id=competition_id,
        season_id=season_id,
        minutes=minutes,
    )
    row.update(overrides)
    return row


def _insert(engine, rows):
    with engine.begin() as connection:
        connection.execute(GKPerformance.__table__.insert(), rows)


# ---------------------------------------------------------------------------
# Estrutura / colunas
# ---------------------------------------------------------------------------

def test_returns_a_dataframe_with_exactly_the_model_columns(sqlite_engine):
    _insert(sqlite_engine, [_row("Keeper A", 1, 2022, 900.0)])
    df = load_gk_performances(engine=sqlite_engine)
    assert list(df.columns) == list(COLUMNS)


def test_columns_match_the_real_gk_performances_model():
    model_columns = tuple(column.name for column in GKPerformance.__table__.columns)
    assert COLUMNS == model_columns


def test_identity_columns_are_present_and_not_dropped(sqlite_engine):
    _insert(sqlite_engine, [_row("Keeper A", 43, 106, 900.0)])
    df = load_gk_performances(engine=sqlite_engine)
    row = df.iloc[0]
    assert row["player_name"] == "Keeper A"
    assert row["competition_id"] == 43
    assert row["season_id"] == 106


# ---------------------------------------------------------------------------
# Sem cálculo de métricas -- só leitura
# ---------------------------------------------------------------------------

def test_values_are_returned_unchanged_from_what_was_stored(sqlite_engine):
    """
    A função só lê -- os valores que saem têm de ser exatamente os que
    foram gravados, sem qualquer transformação aritmética.
    """
    _insert(
        sqlite_engine,
        [_row("Keeper A", 1, 2022, 900.0, save_pct=73.456, shots_faced=42.0)],
    )
    df = load_gk_performances(engine=sqlite_engine)
    row = df.iloc[0]
    assert row["save_pct"] == 73.456
    assert row["shots_faced"] == 42.0


def test_null_metrics_stay_null_not_zero(sqlite_engine):
    """
    Um valor NULL na BD (ex.: sweeper_actions de quem nunca saiu da
    baliza) tem de continuar ausente, nunca virar 0 por acidente da
    leitura.
    """
    _insert(sqlite_engine, [_row("Keeper A", 1, 2022, 900.0, sweeper_actions=None)])
    df = load_gk_performances(engine=sqlite_engine)
    assert pd.isna(df.iloc[0]["sweeper_actions"])


# ---------------------------------------------------------------------------
# Múltiplas linhas / múltiplos contextos
# ---------------------------------------------------------------------------

def test_same_player_in_two_contexts_produces_two_rows(sqlite_engine):
    _insert(
        sqlite_engine,
        [
            _row("Keeper A", 1, 2022, 900.0),
            _row("Keeper A", 2, 2023, 450.0),
        ],
    )
    df = load_gk_performances(engine=sqlite_engine)
    assert len(df) == 2
    assert set(zip(df["competition_id"], df["season_id"])) == {(1, 2022), (2, 2023)}


def test_multiple_players_are_all_returned(sqlite_engine):
    _insert(
        sqlite_engine,
        [
            _row("Keeper A", 1, 2022, 900.0),
            _row("Keeper B", 1, 2022, 450.0),
            _row("Keeper C", 2, 2023, 720.0),
        ],
    )
    df = load_gk_performances(engine=sqlite_engine)
    assert len(df) == 3
    assert set(df["player_name"]) == {"Keeper A", "Keeper B", "Keeper C"}


# ---------------------------------------------------------------------------
# Tabela vazia
# ---------------------------------------------------------------------------

def test_empty_table_returns_empty_dataframe_with_correct_columns(sqlite_engine):
    df = load_gk_performances(engine=sqlite_engine)
    assert df.empty
    assert list(df.columns) == list(COLUMNS)


def test_empty_dataframe_still_supports_downstream_column_checks(sqlite_engine):
    """
    O código que consome isto (streamlit_app.py) faz
    `"minutes" in table.columns` mesmo quando não há linhas -- por isso
    até o resultado vazio tem de ter as colunas certas.
    """
    df = load_gk_performances(engine=sqlite_engine)
    assert "minutes" in df.columns
    assert "player_name" in df.columns


# ---------------------------------------------------------------------------
# DATABASE_URL não configurada
# ---------------------------------------------------------------------------

def test_missing_database_url_raises_a_clear_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        load_gk_performances()
