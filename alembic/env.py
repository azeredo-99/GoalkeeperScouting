"""
Ambiente de execução do Alembic.

`DATABASE_URL` tem de estar exportada no ambiente que corre o Alembic
(não é lida automaticamente de `.env` -- não foi adicionada nenhuma
dependência nova só para isso). Ver o `.env.example` e a nota de
validação desta fase para o comando exato de exportação.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gk_scouting.db.config import get_database_url  # noqa: E402
from gk_scouting.db.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata usada pelo `--autogenerate` em futuras migrações. A migration
# inicial desta fase (versions/0001_create_gk_performances.py) foi escrita
# à mão, não gerada automaticamente -- mas manter isto configurado desde
# já evita reescrever env.py quando a próxima tabela for adicionada.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Gera o SQL das migrações sem ligar a uma base de dados real.

    É o modo usado para validar esta fase sem Docker/Postgres disponíveis:
        alembic upgrade head --sql
    """
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Liga-se a uma base de dados real e aplica as migrações."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
