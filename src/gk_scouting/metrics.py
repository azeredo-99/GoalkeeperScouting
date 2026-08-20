"""
gk_scouting.metrics
-------------------

Transforma eventos StatsBomb em métricas agregadas por guarda-redes.

Versão otimizada:
- evita apply(axis=1);
- reduz loops Python;
- usa groupby/vectorização;
- mantém a mesma API pública.
"""

import numpy as np
import pandas as pd


OWN_GOAL_X = 0.0
OWN_GOAL_Y = 40.0

# Valores de `goalkeeper_type` usados nas metricas de shot stopping.
# Ver a docstring de shot_stopping_metrics() para a justificacao de cada um.
SAVE_TYPES = (
    "Shot Saved",
    "Shot Saved to Post",
)

GOAL_CONCEDED_TYPES = (
    "Goal Conceded",
)

# Remates que nunca exigiram defesa (fora, bloqueados, ao poste, wayward).
NON_SAVE_SHOT_TYPES = (
    "Shot Faced",
)


# Colunas que identificam competicao/epoca num dataset multi-competicao
# (ver download_extended_data.py). Passadas a build_scouting_table() via
# `context_columns` para evitar agregar o mesmo jogador entre competicoes
# ou epocas diferentes.
CONTEXT_COLUMNS = ("competition_id", "season_id")


# ---------------------------------------------------------------------------
# Relogio regulamentar
# ---------------------------------------------------------------------------
#
# No StatsBomb o `minute` REINICIA no inicio regulamentar de cada periodo e
# depois corre pelo tempo de compensacao adentro. Verificado no dataset:
#
#     periodo 1 -> comeca sempre a 0,   termina entre 45 e 59
#     periodo 2 -> comeca sempre a 45,  termina entre 93 e 103
#     periodo 3 -> comeca sempre a 90,  termina entre 105 e 108
#     periodo 4 -> comeca sempre a 105, termina entre 121 e 124
#     periodo 5 -> grandes penalidades
#
# Ou seja, os minutos de periodos consecutivos SOBREPOEM-SE: num jogo o
# periodo 1 foi de 0 a 59 e o periodo 2 recomecou aos 45. E por isso que
# `max(minute)` nao servia como duracao de jogo.
#
# Contamos em minutos regulamentares -- 90 num jogo normal, 120 com
# prolongamento -- que e a convencao do Transfermarkt e do FBref e a unica
# comparavel entre jogos com compensacoes diferentes.

PERIOD_STARTS = {1: 0, 2: 45, 3: 90, 4: 105}
PERIOD_ENDS = {1: 45, 2: 90, 3: 105, 4: 120}

SHOOTOUT_PERIOD = 5

# Cartoes que retiram definitivamente um jogador do campo.
SENDING_OFF_CARDS = ("Red Card", "Second Yellow")

CARD_COLUMNS = ("foul_committed_card", "bad_behaviour_card")


def regulation_minute(period, minute) -> float:
    """
    Converte o relogio de evento para o relogio regulamentar.

    O tempo de compensacao e absorvido pelo fim do periodo: uma substituicao
    aos 95 minutos do periodo 2 conta como tendo acontecido aos 90. Sem isto,
    um titular de um jogo com muita compensacao acumularia mais de 90 minutos
    e deixaria de ser comparavel com um titular de outro jogo.

    Levanta ValueError no periodo de grandes penalidades, que nao e tempo
    de jogo.
    """

    period = int(period)

    if period not in PERIOD_STARTS:
        raise ValueError(
            f"Periodo {period} nao corresponde a tempo de jogo "
            f"(periodos validos: {sorted(PERIOD_STARTS)})."
        )

    return float(
        min(
            max(
                float(minute),
                PERIOD_STARTS[period],
            ),
            PERIOD_ENDS[period],
        )
    )


def match_regulation_duration(
    events: pd.DataFrame,
) -> pd.Series:
    """
    Duracao regulamentar de cada jogo: 90, ou 120 se houve prolongamento.

    O periodo de grandes penalidades e ignorado -- nao e tempo de jogo.
    """

    in_play = events[
        events["period"] != SHOOTOUT_PERIOD
    ]

    if in_play.empty:
        return pd.Series(dtype=float, name="duration")

    last_period = (
        in_play
        .groupby("match_id", sort=False)["period"]
        .max()
    )

    return (
        last_period
        .map(PERIOD_ENDS)
        .astype(float)
        .rename("duration")
    )


def starting_lineups(
    events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Extrai os onzes iniciais dos eventos `Starting XI`.

    Cada jogo tem um `Starting XI` por equipa, e `tactics.lineup` lista
    exatamente os 11 titulares com a posicao de cada um.

    Nao usa `Tactical Shift`, que tambem transporta um `lineup` mas descreve
    uma alteracao tatica a meio do jogo, nao quem comecou.
    """

    if "tactics" not in events.columns:
        return pd.DataFrame(columns=["match_id", "player", "position"])

    starting = events[
        events["type"] == "Starting XI"
    ]

    rows = []

    for match_id, tactics in zip(
        starting["match_id"],
        starting["tactics"],
    ):
        if not isinstance(tactics, dict):
            continue

        for entry in tactics.get("lineup") or []:
            player = (entry.get("player") or {}).get("name")

            if not player:
                continue

            rows.append(
                {
                    "match_id": match_id,
                    "player": player,
                    "position": (entry.get("position") or {}).get("name"),
                }
            )

    return pd.DataFrame(
        rows,
        columns=["match_id", "player", "position"],
    )


def matches_without_lineup(
    events: pd.DataFrame,
) -> list:
    """
    Jogos sem qualquer evento `Starting XI`.

    Nesses jogos e impossivel saber quem comecou, por isso nenhum jogador
    recebe minutos e o jogo fica fora das metricas. Nao ha recurso
    silencioso a logica antiga: esta funcao existe para que o numero de
    jogos afetados seja mensuravel.
    """

    if events.empty:
        return []

    all_matches = set(events["match_id"].dropna().unique())

    lineup = starting_lineups(events)

    with_lineup = (
        set(lineup["match_id"].unique())
        if not lineup.empty
        else set()
    )

    return sorted(all_matches - with_lineup)


def _substitution_times(
    events: pd.DataFrame,
):
    """
    Minuto regulamentar de saida e de entrada, por (jogo, jogador).

    Substituicoes feitas no periodo de grandes penalidades sao ignoradas:
    acontecem depois de o jogo ter terminado e nao alteram minutos jogados.
    """

    empty = pd.DataFrame(
        {
            "match_id": pd.Series(dtype="object"),
            "player": pd.Series(dtype="object"),
            "minute": pd.Series(dtype="float"),
        }
    )

    if "substitution_replacement" not in events.columns:
        return empty.copy(), empty.copy()

    subs = events[
        (events["type"] == "Substitution")
        & (events["period"] != SHOOTOUT_PERIOD)
    ].copy()

    if subs.empty:
        return empty.copy(), empty.copy()

    subs["clock"] = [
        regulation_minute(period, minute)
        for period, minute in zip(subs["period"], subs["minute"])
    ]

    off = (
        subs[["match_id", "player", "clock"]]
        .rename(columns={"clock": "minute"})
        .dropna(subset=["player"])
    )

    on = (
        subs[["match_id", "substitution_replacement", "clock"]]
        .rename(columns={"substitution_replacement": "player", "clock": "minute"})
        .dropna(subset=["player"])
    )

    # Se houver mais do que um registo para o mesmo jogador, fica o mais cedo.
    off = off.groupby(["match_id", "player"], as_index=False)["minute"].min()
    on = on.groupby(["match_id", "player"], as_index=False)["minute"].min()

    return off, on


def _sending_off_times(
    events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Minuto regulamentar em que cada jogador expulso deixou o campo.

    Os eventos `Player Off` NAO sao usados: no dataset todos correspondem a
    saidas temporarias (cada um tem um `Player On` a seguir) e nenhum
    envolve guarda-redes.
    """

    available = [
        column
        for column in CARD_COLUMNS
        if column in events.columns
    ]

    if not available:
        return pd.DataFrame(columns=["match_id", "player", "minute"])

    mask = None

    for column in available:
        column_mask = events[column].isin(SENDING_OFF_CARDS)
        mask = column_mask if mask is None else (mask | column_mask)

    # Ha cartoes mostrados durante o desempate por penaltis. Nao alteram o
    # tempo de jogo de ninguem: o jogo ja terminou.
    sent_off = events[
        mask
        & (events["period"] != SHOOTOUT_PERIOD)
    ].copy()

    if sent_off.empty:
        return pd.DataFrame(columns=["match_id", "player", "minute"])

    sent_off["minute"] = [
        regulation_minute(period, minute)
        for period, minute in zip(sent_off["period"], sent_off["minute"])
    ]

    return (
        sent_off[["match_id", "player", "minute"]]
        .dropna(subset=["player"])
        .groupby(["match_id", "player"], as_index=False)["minute"]
        .min()
    )


def _goalkeepers_by_match(
    events: pd.DataFrame,
    gk_events: pd.DataFrame,
    lineup: pd.DataFrame,
) -> pd.DataFrame:
    """
    Pares (jogo, jogador) em que o jogador atuou como guarda-redes.

    Reune tres sinais, porque nenhum sozinho cobre todos os casos:

        1. titular com posicao `Goalkeeper` no `Starting XI`;
        2. qualquer evento seu com `position == "Goalkeeper"`;
        3. eventos do tipo `Goal Keeper` (via `gk_events`).

    Os sinais 2 e 3 cobrem tanto um suplente que entra a baliza como um
    jogador de campo que vai para a baliza apos uma expulsao.
    """

    frames = []

    if not lineup.empty:
        frames.append(
            lineup.loc[
                lineup["position"] == "Goalkeeper",
                ["match_id", "player"],
            ]
        )

    if "position" in events.columns:
        frames.append(
            events.loc[
                events["position"] == "Goalkeeper",
                ["match_id", "player"],
            ]
        )

    if not gk_events.empty and "match_id" in gk_events.columns:
        frames.append(gk_events[["match_id", "player"]])

    if not frames:
        return pd.DataFrame(columns=["match_id", "player"])

    return (
        pd.concat(frames, ignore_index=True)
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )


def goalkeeper_minutes_by_match(
    events: pd.DataFrame,
    gk_events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Minutos regulamentares de cada guarda-redes em cada jogo.

    Regra:

        entrada = 0 se titular, senao o minuto da substituicao em que entrou
        saida   = o mais cedo entre substituicao, expulsao e fim do jogo
        minutos = saida - entrada

    Um guarda-redes que nao esteja no onze inicial e nunca tenha entrado NAO
    aparece no resultado: ter eventos registados nao prova presenca em campo.
    O mesmo se aplica a jogos sem `Starting XI` (ver `matches_without_lineup`).
    """

    columns = ["match_id", "player", "started", "on", "off", "minutes"]

    if events.empty:
        return pd.DataFrame(columns=columns)

    duration = match_regulation_duration(events)
    lineup = starting_lineups(events)
    keepers = _goalkeepers_by_match(events, gk_events, lineup)

    if keepers.empty:
        return pd.DataFrame(columns=columns)

    if lineup.empty:
        starters = pd.DataFrame(columns=["match_id", "player"])
    else:
        starters = lineup[["match_id", "player"]].drop_duplicates()

    starters = starters.assign(started=True)

    off, on = _substitution_times(events)
    sent_off = _sending_off_times(events)

    frame = (
        keepers
        .merge(starters, on=["match_id", "player"], how="left")
        .merge(on.rename(columns={"minute": "on"}), on=["match_id", "player"], how="left")
        .merge(off.rename(columns={"minute": "off"}), on=["match_id", "player"], how="left")
        .merge(
            sent_off.rename(columns={"minute": "sent_off"}),
            on=["match_id", "player"],
            how="left",
        )
    )

    frame["started"] = frame["started"].fillna(False).astype(bool)
    frame["duration"] = frame["match_id"].map(duration)

    # Os merges acima podem trazer colunas com dtype `object` quando a fonte
    # esta vazia (por exemplo um dataset sem expulsoes). Sem esta conversao,
    # `minutes` herdaria `object` e as divisoes por 90 rebentariam em vez de
    # devolverem NaN.
    for column in ("on", "off", "sent_off", "duration"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    # Sem duracao (jogo so com grandes penalidades) nao ha tempo de jogo.
    frame = frame[frame["duration"].notna()]

    # Entrou em campo como titular, ou ao ser lancado como substituto.
    frame["start"] = np.where(frame["started"], 0.0, frame["on"])
    frame = frame[frame["start"].notna()]

    # Saiu no mais cedo entre substituicao, expulsao e fim do jogo.
    frame["end"] = frame[["off", "sent_off", "duration"]].min(axis=1)

    frame["minutes"] = (
        (frame["end"] - frame["start"])
        .clip(lower=0.0)
        .astype(float)
    )

    return frame[columns].reset_index(drop=True)


def _distance_to_goal_series(
    x: pd.Series,
    y: pd.Series,
) -> pd.Series:
    """Distância vetorizada à baliza própria."""

    x_num = pd.to_numeric(
        x,
        errors="coerce",
    )

    y_num = pd.to_numeric(
        y,
        errors="coerce",
    )

    return np.hypot(
        x_num - OWN_GOAL_X,
        y_num - OWN_GOAL_Y,
    )


def compute_minutes_played(
    events: pd.DataFrame,
    gk_events: pd.DataFrame,
) -> pd.Series:
    """
    Minutos regulamentares jogados por cada guarda-redes.

    Soma, por jogador, os minutos de `goalkeeper_minutes_by_match()`, que
    derivam do `Starting XI` e das substituicoes.

    Substitui a estimativa anterior, que atribuia a duracao completa do jogo
    a qualquer guarda-redes com pelo menos um evento nesse jogo -- e que por
    isso dava 90 minutos a um suplente que entrasse aos 85.

    Guarda-redes que nunca entraram em campo nao aparecem no resultado.
    """

    if events.empty or gk_events.empty:
        return pd.Series(
            dtype=float,
            name="minutes",
        )

    per_match = goalkeeper_minutes_by_match(
        events,
        gk_events,
    )

    if per_match.empty:
        return pd.Series(
            dtype=float,
            name="minutes",
        )

    return (
        per_match
        .groupby("player", sort=False)["minutes"]
        .sum()
        .rename("minutes")
    )


def sweeper_keeper_metrics(
    gk_events: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas de sweeper-keeper sem apply."""

    if gk_events.empty:
        return pd.DataFrame(
            columns=[
                "sweeper_actions",
                "avg_distance_from_goal",
                "max_distance_from_goal",
            ]
        )

    sweeper = gk_events[
        gk_events["goalkeeper_type"]
        == "Keeper Sweeper"
    ].copy()

    if sweeper.empty:

        return pd.DataFrame(
            columns=[
                "sweeper_actions",
                "avg_distance_from_goal",
                "max_distance_from_goal",
            ]
        )

    sweeper["distance_from_goal"] = (
        _distance_to_goal_series(
            sweeper["x"],
            sweeper["y"],
        )
    )

    return (
        sweeper
        .groupby(
            "player",
            sort=False,
        )
        .agg(
            sweeper_actions=(
                "player",
                "size",
            ),
            avg_distance_from_goal=(
                "distance_from_goal",
                "mean",
            ),
            max_distance_from_goal=(
                "distance_from_goal",
                "max",
            ),
        )
    )


def shot_stopping_metrics(
    gk_events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula metricas de shot stopping.

    Categorias de `goalkeeper_type` (verificadas no dataset ligando cada
    evento ao `shot_outcome` do remate correspondente via `related_events`):

        Shot Saved             -> defesa a remate enquadrado
        Shot Saved to Post     -> defesa a remate enquadrado (bate no poste)
        Goal Conceded          -> golo sofrido
        Shot Faced             -> remate NAO enquadrado ou bloqueado
                                  (Off T / Blocked / Post / Wayward)
        Shot Saved Off Target  -> defesa a remate que ia para fora
        Penalty Saved/Conceded -> grandes penalidades

    Estas categorias sao mutuamente exclusivas: cada remate produz no
    maximo um evento de guarda-redes (confirmado -- zero instantes com
    mais do que um evento GK no mesmo timestamp).

    Decisoes deliberadas:

    * `Shot Faced` NAO entra no denominador da percentagem de defesas.
      Sao remates que nunca exigiram defesa, por isso incluí-los media a
      pontaria do adversario, nao a competencia do guarda-redes.
    * `Shot Saved Off Target` fica de fora: o remate ia para fora e nunca
      seria golo, logo nao e um remate enquadrado.
    * As grandes penalidades ficam de fora. A maioria pertence a desempates
      por penaltis, que por convencao nao contam para a percentagem de
      defesas.
    """

    if gk_events.empty:
        return pd.DataFrame(
            columns=[
                "shots_faced",
                "shots_saved",
                "goals_conceded",
                "save_pct",
            ]
        )

    type_series = gk_events[
        "goalkeeper_type"
    ]

    player_series = gk_events[
        "player"
    ]

    def _count(types):
        return (
            type_series.isin(types)
            .groupby(
                player_series,
                sort=False,
            )
            .sum()
        )

    shots_saved = _count(SAVE_TYPES)
    goals_conceded = _count(GOAL_CONCEDED_TYPES)
    shots_not_on_target = _count(NON_SAVE_SHOT_TYPES)

    df = pd.concat(
        [
            shots_saved.rename(
                "shots_saved"
            ),
            goals_conceded.rename(
                "goals_conceded"
            ),
            shots_not_on_target.rename(
                "shots_not_on_target"
            ),
        ],
        axis=1,
    ).fillna(0.0)

    # Remates enquadrados = os que o guarda-redes defendeu + os que sofreu.
    # E este o denominador correto da percentagem de defesas.
    shots_on_target = (
        df["shots_saved"]
        + df["goals_conceded"]
    )

    # `shots_faced` = todos os remates enfrentados, enquadrados ou nao.
    df["shots_faced"] = (
        shots_on_target
        + df["shots_not_on_target"]
    )

    # Sem remates enquadrados a percentagem e indefinida (NaN), nunca 0 nem
    # 100: um guarda-redes que nao enfrentou remates enquadrados nao tem
    # percentagem de defesas, e tratar isso como 0% penalizava-o de forma
    # incorreta nas comparacoes.
    df["save_pct"] = np.where(
        shots_on_target > 0,
        (
            df["shots_saved"]
            / shots_on_target
            * 100
        ),
        np.nan,
    )

    return df[
        [
            "shots_faced",
            "shots_saved",
            "goals_conceded",
            "save_pct",
        ]
    ]


def distribution_metrics(
    gk_passes: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas de distribuição sem loops."""

    if gk_passes.empty:
        return pd.DataFrame(
            columns=[
                "total_passes",
                "pass_success_pct",
                "avg_pass_length",
                "long_ball_pct",
            ]
        )

    df = gk_passes.copy()

    outcome = df[
        "pass_outcome"
    ]

    df["is_success"] = (
        outcome.isna()
    )

    df["is_long"] = (
        pd.to_numeric(
            df["pass_length"],
            errors="coerce",
        )
        > 40
    )

    return (
        df
        .groupby(
            "player",
            sort=False,
        )
        .agg(
            total_passes=(
                "player",
                "size",
            ),
            pass_success_pct=(
                "is_success",
                "mean",
            ),
            avg_pass_length=(
                "pass_length",
                "mean",
            ),
            long_ball_pct=(
                "is_long",
                "mean",
            ),
        )
        .assign(
            pass_success_pct=lambda frame:
                frame["pass_success_pct"] * 100,
            long_ball_pct=lambda frame:
                frame["long_ball_pct"] * 100,
        )
    )


def _finalize_table(minutes, sweeper, shots, dist) -> pd.DataFrame:
    """
    Junta as quatro peças de métricas numa única tabela por jogador.

    Extraído de build_scouting_table() para ser reutilizado tanto no
    agregado normal (uma linha por jogador) como em cada fatia de
    competição/época, sem duplicar a lógica de montagem nem o cálculo
    dos p90.
    """

    table = pd.concat(
        [
            minutes,
            sweeper,
            shots,
            dist,
        ],
        axis=1,
    )

    table.index.name = "player"

    table["sweeper_actions_p90"] = np.where(
        table["minutes"] > 0,
        (
            table["sweeper_actions"]
            / table["minutes"]
            * 90
        ),
        np.nan,
    )

    table["shots_faced_p90"] = np.where(
        table["minutes"] > 0,
        (
            table["shots_faced"]
            / table["minutes"]
            * 90
        ),
        np.nan,
    )

    return table


def build_scouting_table(
    events: pd.DataFrame,
    gk_events: pd.DataFrame,
    gk_passes: pd.DataFrame,
    context_columns=None,
) -> pd.DataFrame:
    """
    Junta todas as métricas numa única tabela por guarda-redes.

    Por omissão (`context_columns=None`) o comportamento é idêntico ao
    anterior a esta alteração: uma linha por jogador, agregando tudo o
    que existir em `events`/`gk_events`/`gk_passes`. Isto significa que,
    num dataset que abrange várias competições ou épocas, um guarda-redes
    presente em mais do que uma fica com uma única linha que MISTURA os
    contextos -- é esse o comportamento histórico, preservado aqui de
    propósito para não alterar a aplicação existente.

    Para evitar essa mistura, passa `context_columns` (por exemplo
    `CONTEXT_COLUMNS`, ou seja `("competition_id", "season_id")`). Nesse
    caso a tabela passa a ter um índice `MultiIndex` de
    `(player, *context_columns)`, com uma linha por combinação realmente
    observada. As quatro funções de métricas (`compute_minutes_played`,
    `sweeper_keeper_metrics`, `shot_stopping_metrics`,
    `distribution_metrics`) não são alteradas: são chamadas, sem
    modificação, uma vez por cada fatia de eventos filtrada por
    `match_id`.

    Se nenhuma das colunas pedidas em `context_columns` existir em
    `events` (por exemplo `events_full_wc2022.pkl`, que não tem
    competição/época porque é de uma só competição), esta função
    degrada-se de forma explícita para o comportamento por omissão --
    NÃO levanta erro, e devolve a mesma tabela de sempre, com índice
    simples por jogador.
    """

    available_context = [
        column
        for column in (context_columns or [])
        if column in events.columns
    ]

    if not available_context:
        minutes = compute_minutes_played(events, gk_events)
        sweeper = sweeper_keeper_metrics(gk_events)
        shots = shot_stopping_metrics(gk_events)
        dist = distribution_metrics(gk_passes)

        table = _finalize_table(minutes, sweeper, shots, dist)

        return table.sort_values(
            "minutes",
            ascending=False,
        )

    # match_id identifica univocamente um (competition_id, season_id) --
    # por isso a fonte de verdade do contexto e sempre `events`, nunca
    # gk_events/gk_passes (que podem ter sido gerados por um loader mais
    # antigo sem essas colunas).
    match_context = (
        events[["match_id", *available_context]]
        .drop_duplicates(subset="match_id")
    )

    groups = (
        match_context
        .groupby(available_context, sort=False)["match_id"]
        .apply(list)
    )

    slices = []

    for combo, match_ids in groups.items():
        if not isinstance(combo, tuple):
            combo = (combo,)

        match_ids = set(match_ids)

        events_slice = events[events["match_id"].isin(match_ids)]
        gk_events_slice = gk_events[gk_events["match_id"].isin(match_ids)]
        gk_passes_slice = gk_passes[gk_passes["match_id"].isin(match_ids)]

        minutes = compute_minutes_played(events_slice, gk_events_slice)
        sweeper = sweeper_keeper_metrics(gk_events_slice)
        shots = shot_stopping_metrics(gk_events_slice)
        dist = distribution_metrics(gk_passes_slice)

        slice_table = _finalize_table(minutes, sweeper, shots, dist)

        if slice_table.empty:
            continue

        for column, value in zip(available_context, combo):
            slice_table[column] = value

        slices.append(slice_table)

    if not slices:
        empty_index = pd.MultiIndex.from_tuples(
            [],
            names=["player", *available_context],
        )
        return pd.DataFrame(index=empty_index)

    table = (
        pd.concat(slices, axis=0)
        .reset_index()
        .set_index(["player", *available_context])
    )

    return table.sort_values(
        "minutes",
        ascending=False,
    )