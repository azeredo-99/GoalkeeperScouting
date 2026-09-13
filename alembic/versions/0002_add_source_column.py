"""add source column to gk_performances

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-13

Adiciona `source` a `gk_performances` para distinguir explicitamente
linhas calculadas a partir de eventos StatsBomb (evento a evento, via
metrics.py) de linhas importadas de estatísticas já agregadas de outra
fonte (ex.: FBref). As duas fontes definem métricas com o mesmo nome de
forma diferente -- esta coluna existe para que nunca sejam misturadas
num peer group de benchmark sem isso ser explícito.

Backfill: todas as linhas existentes (todas StatsBomb) recebem
"statsbomb" via server_default, para que a migração não perca
proveniência de dados já gravados.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "gk_performances",
        sa.Column(
            "source",
            sa.String(),
            nullable=False,
            server_default="statsbomb",
        ),
    )


def downgrade() -> None:
    op.drop_column("gk_performances", "source")
