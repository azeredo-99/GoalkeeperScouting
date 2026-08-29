"""
Funções puras para o modo Discovery (pesquisa por nome + descoberta por
filtro).

Vivem fora de `streamlit_app.py` pela mesma razão que `presentation.py`:
são testáveis sem precisar de Streamlit nem de ligação à BD. Nenhuma
função aqui calcula uma métrica nova -- trabalham sobre `performances`,
que já vem materializada de `gk_performances`
(ver `gk_scouting.db.repository.load_gk_performances`), e sobre o mapa
de mercado que a app já constrói (`build_performance_market_map`, em
`streamlit_app.py`) -- não é criada nenhuma fonte de dados nova.

Cada linha de `performances` continua a ser um
(player_name, competition_id, season_id) distinto em todas estas
funções: nenhuma agrega ou mistura contextos diferentes do mesmo
jogador.
"""

import pandas as pd

from .market_data import calculate_age


def search_by_name(performances: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Pesquisa por nome, parcial e sem distinguir maiúsculas/minúsculas.

    Devolve TODAS as linhas de contexto do(s) jogador(es) encontrados --
    um jogador com várias competições/épocas aparece em várias linhas,
    nunca agregado.

    Uma pesquisa vazia (ou só espaços) devolve um resultado vazio, não a
    tabela inteira -- para não confundir "ainda não pesquisei" com
    "estes são todos os resultados".
    """
    query = (query or "").strip()

    if not query or performances.empty:
        return performances.iloc[0:0]

    mask = (
        performances["player_name"]
        .str.casefold()
        .str.contains(query.casefold(), regex=False, na=False)
    )
    return performances[mask].reset_index(drop=True)


def enrich_with_market(
    performances: pd.DataFrame,
    market_lookup: dict,
    season_reference_dates: dict | None = None,
) -> pd.DataFrame:
    """
    Acrescenta `current_club_name`, `market_value_in_eur` e `age` a cada
    linha, a partir de `market_lookup` (mapa player_name -> linha de
    mercado, já resolvido pelo matching StatsBomb<->Transfermarkt
    existente -- não é uma fonte de dados nova, é o mapa que a app já
    constrói).

    `season_reference_dates` é um mapa opcional
    `(competition_id, season_id) -> pd.Timestamp` (ver
    `market_data.season_reference_date`), para que a idade seja a da
    própria época da linha -- nunca a idade atual, que não tem relação
    com uma amostra de desempenho histórica. Sem este mapa, cada idade
    cai na omissão de `calculate_age` (idade atual); o chamador deve
    passá-lo sempre que os dados forem de épocas passadas, que é o caso
    de todo este projeto.

    Um jogador sem correspondência de mercado fica com essas três
    colunas a `None`/`NaN`, nunca removido nem inventado.
    """
    columns = ["current_club_name", "market_value_in_eur", "age"]

    if performances.empty:
        return performances.assign(**{column: pd.Series(dtype="object") for column in columns})

    def _market_row(name):
        return market_lookup.get(name)

    def _club(name):
        row = _market_row(name)
        if row is None:
            return None
        club = row.get("current_club_name")
        return None if pd.isna(club) else club

    def _value(name):
        row = _market_row(name)
        return None if row is None else row.get("market_value_in_eur")

    def _age(perf_row):
        market_row = _market_row(perf_row["player_name"])
        if market_row is None:
            return None
        as_of = None
        if season_reference_dates is not None:
            as_of = season_reference_dates.get((perf_row["competition_id"], perf_row["season_id"]))
        return calculate_age(market_row.get("date_of_birth"), as_of=as_of)

    result = performances.copy()
    result["current_club_name"] = result["player_name"].map(_club)
    result["market_value_in_eur"] = result["player_name"].map(_value)
    result["age"] = result.apply(_age, axis=1)
    return result


def filter_candidates(
    df: pd.DataFrame,
    *,
    competition_id: int | None = None,
    season_id: int | None = None,
    min_minutes: float | None = None,
    max_age: float | None = None,
    min_market_value: float | None = None,
    max_market_value: float | None = None,
    min_save_pct: float | None = None,
    min_sweeper_actions_p90: float | None = None,
    min_pass_success_pct: float | None = None,
    min_long_ball_pct: float | None = None,
) -> pd.DataFrame:
    """
    Aplica filtros explícitos, um de cada vez, todos opcionais.

    `None` num filtro significa "sem restrição nesse critério" -- a
    escolha explícita de "todas as competições/épocas" na UI mapeia
    para `competition_id=None`/`season_id=None`, nunca para um valor por
    omissão escondido.

    A idade e o valor de mercado só conseguem filtrar linhas onde esses
    dados existem: um jogador sem correspondência de mercado fica de
    fora quando um desses filtros está ativo (não pode ser avaliado,
    por isso não passa), mas continua incluído quando esses filtros não
    são usados.

    Os filtros de performance (Discovery 2.0) usam exatamente as mesmas
    colunas já calculadas por `metrics.py` -- nenhum recálculo, nenhuma
    métrica nova. Mesma regra de missing values: uma linha sem o dado
    (ex.: sem sweeper actions) não pode satisfazer um mínimo, por isso
    fica de fora quando esse filtro está ativo.
    """

    result = df

    if competition_id is not None:
        result = result[result["competition_id"] == competition_id]

    if season_id is not None:
        result = result[result["season_id"] == season_id]

    if min_minutes is not None:
        result = result[result["minutes"] >= min_minutes]

    if max_age is not None:
        result = result[result["age"].notna() & (result["age"] <= max_age)]

    if min_market_value is not None:
        result = result[
            result["market_value_in_eur"].notna()
            & (result["market_value_in_eur"] >= min_market_value)
        ]

    if max_market_value is not None:
        result = result[
            result["market_value_in_eur"].notna()
            & (result["market_value_in_eur"] <= max_market_value)
        ]

    if min_save_pct is not None:
        result = result[result["save_pct"].notna() & (result["save_pct"] >= min_save_pct)]

    if min_sweeper_actions_p90 is not None:
        result = result[
            result["sweeper_actions_p90"].notna()
            & (result["sweeper_actions_p90"] >= min_sweeper_actions_p90)
        ]

    if min_pass_success_pct is not None:
        result = result[
            result["pass_success_pct"].notna()
            & (result["pass_success_pct"] >= min_pass_success_pct)
        ]

    if min_long_ball_pct is not None:
        result = result[
            result["long_ball_pct"].notna() & (result["long_ball_pct"] >= min_long_ball_pct)
        ]

    return result.reset_index(drop=True)


def available_competitions(performances: pd.DataFrame) -> list[int]:
    """Valores distintos de competition_id realmente presentes nos dados."""
    if performances.empty:
        return []
    return sorted(performances["competition_id"].dropna().unique().tolist())


def available_seasons(performances: pd.DataFrame, competition_id: int | None = None) -> list[int]:
    """
    Valores distintos de season_id presentes nos dados.

    Se `competition_id` for indicado, restringe às épocas dessa
    competição -- para o seletor de época não oferecer combinações que
    não existem.
    """
    if performances.empty:
        return []

    rows = performances
    if competition_id is not None:
        rows = rows[rows["competition_id"] == competition_id]

    return sorted(rows["season_id"].dropna().unique().tolist())
