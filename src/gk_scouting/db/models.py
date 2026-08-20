"""
Modelo SQLAlchemy para `gk_performances`.

Mapeia exatamente o output real e confirmado de
`build_scouting_table(events, gk_events, gk_passes, context_columns=CONTEXT_COLUMNS)`
(ver `gk_scouting.metrics`) -- nenhuma coluna aqui foi inventada; todas
foram verificadas empiricamente a correr essa função sobre
`data/events_extended.pkl`.

Decisão pendente (registada, não resolvida aqui): a chave de identidade do
jogador é o NOME (`player_name`), não um `player_id` estável. O
`player_id` do StatsBomb existe ao nível do evento (`gk_events`/
`gk_passes`, desde o P0-5) mas é descartado pelos `groupby("player", ...)`
internos de `metrics.py` antes de chegar à tabela final -- por isso não
pode ser usado aqui sem alterar essa lógica, o que ficou fora do âmbito
desta fase. Isto reintroduz o mesmo risco já apontado na auditoria
original (M4: nomes homónimos colidem). Resolver quando a tabela
`players` for criada.
"""

from sqlalchemy import Float, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GKPerformance(Base):
    """
    Uma linha = um guarda-redes, numa competição, numa época.

    Chave única: (player_name, competition_id, season_id) -- corresponde
    exatamente ao índice `MultiIndex` que `build_scouting_table` produz
    quando chamada com `context_columns=CONTEXT_COLUMNS`.
    """

    __tablename__ = "gk_performances"
    __table_args__ = (
        PrimaryKeyConstraint(
            "player_name", "competition_id", "season_id",
            name="pk_gk_performances",
        ),
    )

    # --- identidade -----------------------------------------------------
    player_name: Mapped[str] = mapped_column(String, nullable=False)
    competition_id: Mapped[int] = mapped_column(Integer, nullable=False)
    season_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- minutos (sempre presente: um jogador só aparece na tabela se
    #     tiver minutos -- ver goalkeeper_minutes_by_match em metrics.py) --
    minutes: Mapped[float] = mapped_column(Float, nullable=False)

    # --- shot stopping ----------------------------------------------------
    shots_faced: Mapped[float | None] = mapped_column(Float, nullable=True)
    shots_saved: Mapped[float | None] = mapped_column(Float, nullable=True)
    goals_conceded: Mapped[float | None] = mapped_column(Float, nullable=True)
    save_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    shots_faced_p90: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- sweeper keeper -----------------------------------------------------
    # Nullable por desenho: um guarda-redes que nunca saiu da baliza não
    # aparece em sweeper_keeper_metrics() (ver M5/S3, ainda por resolver
    # no domínio -- não é um bug de persistência).
    sweeper_actions: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_distance_from_goal: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_distance_from_goal: Mapped[float | None] = mapped_column(Float, nullable=True)
    sweeper_actions_p90: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- distribuição -----------------------------------------------------
    total_passes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pass_success_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_pass_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    long_ball_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return (
            f"GKPerformance(player_name={self.player_name!r}, "
            f"competition_id={self.competition_id}, season_id={self.season_id}, "
            f"minutes={self.minutes})"
        )
