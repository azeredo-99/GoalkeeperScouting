"""create gk_performances

Revision ID: 0001
Revises:
Create Date: 2026-08-20

Cria a tabela gk_performances, mapeando o output confirmado de
build_scouting_table(events, gk_events, gk_passes, context_columns=CONTEXT_COLUMNS)
(ver gk_scouting.db.models.GKPerformance para a justificação de cada
coluna e a decisão pendente sobre player_name vs. player_id).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gk_performances",
        sa.Column("player_name", sa.String(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("minutes", sa.Float(), nullable=False),
        sa.Column("shots_faced", sa.Float(), nullable=True),
        sa.Column("shots_saved", sa.Float(), nullable=True),
        sa.Column("goals_conceded", sa.Float(), nullable=True),
        sa.Column("save_pct", sa.Float(), nullable=True),
        sa.Column("shots_faced_p90", sa.Float(), nullable=True),
        sa.Column("sweeper_actions", sa.Float(), nullable=True),
        sa.Column("avg_distance_from_goal", sa.Float(), nullable=True),
        sa.Column("max_distance_from_goal", sa.Float(), nullable=True),
        sa.Column("sweeper_actions_p90", sa.Float(), nullable=True),
        sa.Column("total_passes", sa.Integer(), nullable=True),
        sa.Column("pass_success_pct", sa.Float(), nullable=True),
        sa.Column("avg_pass_length", sa.Float(), nullable=True),
        sa.Column("long_ball_pct", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint(
            "player_name", "competition_id", "season_id",
            name="pk_gk_performances",
        ),
    )


def downgrade() -> None:
    op.drop_table("gk_performances")
