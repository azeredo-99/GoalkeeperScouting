"""
gk_scouting.visuals
-------------------

Visualizações centrais:
- radar comparativo;
- mapa de ações sweeper-keeper.

"""

import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch


BG = "#0f172a"
PANEL = "#1e293b"
GRID = "#334155"
TEXT = "#e2e8f0"

ACCENT = [
    "#22c55e",
    "#f59e0b",
    "#38bdf8",
    "#f472b6",
]


RADAR_METRICS = {
    "save_pct": (
        "Eficácia defesas (%)",
        True,
    ),
    "sweeper_actions_p90": (
        "Ações Sweeper /90",
        True,
    ),
    "avg_distance_from_goal": (
        "Distância média à baliza",
        True,
    ),
    "pass_success_pct": (
        "Eficácia de passe (%)",
        True,
    ),
    "long_ball_pct": (
        "% Bola longa",
        True,
    ),
}


def _normalize_series(
    series,
) -> np.ndarray:
    """
    Min-max normalization para 0-100.

    Mantém compatibilidade com o radar existente.
    """

    values = (
        series
        .astype(float)
        .to_numpy()
    )

    finite = np.isfinite(values)

    if not finite.any():
        return np.full(
            values.shape,
            np.nan,
        )

    lo = np.nanmin(values)
    hi = np.nanmax(values)

    if hi == lo:
        return np.full(
            values.shape,
            50.0,
        )

    return (
        (values - lo)
        / (hi - lo)
        * 100
    )


def _build_radar_scores(
    table,
    metrics,
) -> dict[str, np.ndarray]:
    """
    Normaliza todas as métricas uma única vez.
    """

    scores = {}

    for metric in metrics:

        scores[metric] = (
            _normalize_series(
                table[metric]
            )
        )

    return scores


def plot_radar(
    table,
    players,
    out_path,
):
    """
    Desenha o radar comparando jogadores.

    `players` deve conter nomes existentes no índice da tabela.
    """

    metrics = list(
        RADAR_METRICS.keys()
    )

    labels = [
        RADAR_METRICS[m][0]
        for m in metrics
    ]

    # Apenas jogadores que existem.
    valid_players = [
        player
        for player in players
        if player in table.index
    ]

    if not valid_players:
        raise ValueError(
            "Nenhum jogador válido para o radar."
        )

    # Calculamos as normalizações apenas uma vez.
    scores = _build_radar_scores(
        table,
        metrics,
    )

    n = len(metrics)

    angles = np.linspace(
        0,
        2 * np.pi,
        n,
        endpoint=False,
    ).tolist()

    angles += angles[:1]

    fig, ax = plt.subplots(
        figsize=(8, 8),
        subplot_kw={
            "polar": True,
        },
    )

    fig.patch.set_facecolor(
        BG
    )

    ax.set_facecolor(
        PANEL
    )

    for i, player in enumerate(
        valid_players
    ):

        row_index = table.index.get_loc(
            player
        )

        values = [
            scores[metric][row_index]
            for metric in metrics
        ]

        # Evitar problemas com NaN.
        values = [
            0 if not np.isfinite(value)
            else float(value)
            for value in values
        ]

        values += values[:1]

        color = ACCENT[
            i % len(ACCENT)
        ]

        ax.plot(
            angles,
            values,
            color=color,
            linewidth=2,
            label=player,
        )

        ax.fill(
            angles,
            values,
            color=color,
            alpha=0.15,
        )

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        labels,
        color=TEXT,
        fontsize=10,
    )

    ax.set_yticks(
        [20, 40, 60, 80, 100]
    )

    ax.set_yticklabels([])

    ax.spines[
        "polar"
    ].set_color(
        GRID
    )

    ax.grid(
        color=GRID,
        alpha=0.5,
    )

    ax.set_theta_offset(
        np.pi / 2
    )

    ax.set_theta_direction(
        -1
    )

    plt.title(
        "Perfil Comparativo de Guarda-Redes\n"
        "(percentil dentro da amostra analisada)",
        color=TEXT,
        fontsize=13,
        pad=30,
    )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.3, 1.15),
        facecolor=PANEL,
        edgecolor="none",
        labelcolor=TEXT,
    )

    fig.savefig(
        out_path,
        facecolor=BG,
        dpi=120,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )


def plot_sweeper_map(
    gk_events,
    player,
    out_path,
):
    """
    Desenha o campo com as ações Keeper Sweeper de um jogador.
    """

    if gk_events.empty:
        raise ValueError(
            "Não existem eventos de guarda-redes."
        )

    mask = (
        gk_events["player"].eq(player)
        & gk_events["goalkeeper_type"].eq(
            "Keeper Sweeper"
        )
    )

    df = gk_events.loc[
        mask,
        [
            "x",
            "y",
            "goalkeeper_outcome",
        ],
    ].copy()

    if df.empty:
        raise ValueError(
            f"Não existem ações Keeper Sweeper para {player}."
        )

    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=BG,
        line_color=GRID,
        half=False,
    )

    fig, ax = pitch.draw(
        figsize=(10, 7)
    )

    fig.set_facecolor(
        BG
    )

    outcomes = (
        df["goalkeeper_outcome"]
        .fillna("Outro")
    )

    unique_outcomes = (
        outcomes.unique()
    )

    colors = {
        outcome:
        ACCENT[i % len(ACCENT)]
        for i, outcome in enumerate(
            unique_outcomes
        )
    }

    for outcome in unique_outcomes:

        sub = df.loc[
            outcomes.eq(outcome)
        ]

        pitch.scatter(
            sub["x"],
            sub["y"],
            ax=ax,
            s=220,
            color=colors[outcome],
            edgecolors="white",
            linewidth=1,
            label=outcome,
            zorder=3,
        )

    ax.legend(
        facecolor=PANEL,
        edgecolor="none",
        labelcolor=TEXT,
        loc="upper right",
    )

    plt.title(
        f"Ações de Sweeper-Keeper — {player}",
        color=TEXT,
        fontsize=14,
        pad=10,
    )

    fig.savefig(
        out_path,
        facecolor=BG,
        dpi=120,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )