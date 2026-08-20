"""
Goalkeeper Scouting — Frontend
--------------------------------

A lógica de dados/performance é mantida; em desenvolvimento:
- navegação;
- pesquisa;
- cards;
- hierarquia visual;
- comparação;
- semelhantes;
- responsividade;
- legibilidade.
"""

import html
import os
import unicodedata

import pandas as pd
import streamlit as st

import _bootstrap  # noqa: F401  (coloca src/ no sys.path)

from gk_scouting.db.repository import load_gk_performances
from gk_scouting.market_data import get_goalkeepers
from gk_scouting.player_matching import (
    create_name_index,
    match_players,
)
# plot_sweeper_map não é usado nesta fase: precisa de coordenadas de
# ações individuais (gk_events), que a app já não carrega desde a
# Fase 1 (só lê gk_performances, agregada). Ver nota no Player Profile.
from gk_scouting.visuals import plot_radar
from gk_scouting.similarity_engine import (
    STYLE_FEATURES,
    default_min_minutes,
    find_similar_goalkeepers,
    explain_similarity,
    normalise_dimension_weights,
)
from gk_scouting.presentation import (
    context_label,
    format_count,
    format_distance_m,
    format_percentage,
    format_rate_p90,
    player_context_rows,
    NO_ACTIONS_LABEL,
)
from gk_scouting.discovery import (
    available_competitions,
    available_seasons,
    enrich_with_market,
    filter_candidates,
    search_by_name,
)
from gk_scouting.comparison import build_comparison_table
from gk_scouting.similarity_view import build_similarity_rows, reference_context


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Goalkeeper Scouting",
    page_icon="🧤",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# FRONTEND THEME
# =========================================================

st.markdown(
    """
    <style>
        :root {
            --gk-navy: #0f172a;
            --gk-blue: #2563eb;
            --gk-blue-dark: #1d4ed8;
            --gk-bg: #f8fafc;
            --gk-panel: #ffffff;
            --gk-border: #e2e8f0;
            --gk-muted: #64748b;
            --gk-text: #0f172a;
            --gk-soft: #eff6ff;
            --gk-green: #16a34a;
        }

        .stApp {
            background:
                linear-gradient(
                    180deg,
                    #f8fafc 0%,
                    #ffffff 260px
                );
        }

        .block-container {
            max-width: 1500px;
            padding-top: 1.4rem;
            padding-bottom: 4rem;
        }

        /* Top navigation */
        div[data-testid="stRadio"] > div {
            gap: 0.45rem;
        }

        div[data-testid="stRadio"] label {
            background: #ffffff;
            border: 1px solid var(--gk-border);
            border-radius: 10px;
            padding: 0.45rem 0.85rem;
            transition: all 0.15s ease;
        }

        div[data-testid="stRadio"] label:hover {
            border-color: #bfdbfe;
            background: #f8fbff;
        }

        /* Native metrics */
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--gk-border);
            border-radius: 12px;
            padding: 0.9rem 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--gk-muted);
        }

        /* Input fields */
        div[data-baseweb="input"] > div {
            border-radius: 10px;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 9px;
            font-weight: 600;
        }

        /* Dataframe */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--gk-border);
            border-radius: 12px;
            overflow: hidden;
        }

        /* Cards */
        .gk-hero {
            background: linear-gradient(
                135deg,
                #0f172a 0%,
                #1e293b 100%
            );
            color: #ffffff;
            border-radius: 18px;
            padding: 1.5rem 1.6rem;
            margin: 0.5rem 0 1rem 0;
            box-shadow:
                0 12px 30px rgba(15, 23, 42, 0.14);
        }

        .gk-hero-title {
            font-size: 1.7rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 0.35rem;
        }

        .gk-hero-subtitle {
            color: #cbd5e1;
            font-size: 0.95rem;
        }

        .gk-section-title {
            font-size: 1.15rem;
            font-weight: 750;
            color: var(--gk-text);
            margin: 0.4rem 0 0.6rem 0;
        }

        .gk-section-note {
            color: var(--gk-muted);
            font-size: 0.88rem;
            margin-bottom: 0.9rem;
        }

        .gk-result {
            background: #ffffff;
            border: 1px solid var(--gk-border);
            border-radius: 11px;
            padding: 0.7rem 0.9rem;
            margin: 0.35rem 0;
        }

        .gk-result-name {
            font-weight: 700;
            color: var(--gk-text);
        }

        .gk-result-meta {
            color: var(--gk-muted);
            font-size: 0.82rem;
        }

        .gk-kpi-label {
            color: var(--gk-muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .gk-kpi-value {
            color: var(--gk-text);
            font-size: 1.45rem;
            font-weight: 800;
            margin-top: 0.15rem;
        }

        .gk-badge {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            background: var(--gk-soft);
            color: var(--gk-blue-dark);
            font-size: 0.75rem;
            font-weight: 700;
        }

        /* Reduce excessive vertical whitespace */
        hr {
            border-color: var(--gk-border);
            margin: 1rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def normalize_search_text(text):
    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        str(text).lower().strip(),
    )

    return "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )


def esc(value):
    """
    Escapa um valor antes de o interpolar em HTML.

    Nomes de jogadores e de clubes vem de um CSV externo que nao
    controlamos; sem escaping, qualquer marcacao nesses campos seria
    executada no browser (o Streamlit nao escapa dentro de
    `unsafe_allow_html=True`).
    """

    if value is None or pd.isna(value):
        return "N/A"

    return html.escape(str(value))


def format_market_value(value):
    if pd.isna(value):
        return "N/A"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if value >= 1_000_000:
        millions = value / 1_000_000
        if millions >= 10:
            return f"€{millions:.0f}M"
        return f"€{millions:.1f}M"

    if value >= 1_000:
        return f"€{value / 1_000:.0f}K"

    return f"€{value:.0f}"


def calculate_age(date_of_birth):
    if pd.isna(date_of_birth):
        return None

    try:
        dob = pd.to_datetime(date_of_birth)
        today = pd.Timestamp.today()

        return (
            today.year
            - dob.year
            - (
                (today.month, today.day)
                < (dob.month, dob.day)
            )
        )
    except Exception:
        return None


def prepare_market_df(df):
    df = df.copy()

    if "normalized_name" not in df.columns:
        df["normalized_name"] = (
            df["name"]
            .fillna("")
            .map(normalize_search_text)
        )

    if "market_value_in_eur" in df.columns:
        df["market_value_in_eur"] = pd.to_numeric(
            df["market_value_in_eur"],
            errors="coerce",
        )

    return df


def search_market_players(
    market_df,
    query,
    limit=20,
):
    if market_df.empty:
        return market_df

    query = normalize_search_text(query)

    if not query:
        return market_df.head(0)

    starts = market_df[
        market_df["normalized_name"]
        .str.startswith(
            query,
            na=False,
        )
    ]

    contains = market_df[
        market_df["normalized_name"]
        .str.contains(
            query,
            regex=False,
            na=False,
        )
        &
        ~market_df["normalized_name"]
        .str.startswith(
            query,
            na=False,
        )
    ]

    starts = starts.sort_values(
        "market_value_in_eur",
        ascending=False,
        na_position="last",
    )

    contains = contains.sort_values(
        "market_value_in_eur",
        ascending=False,
        na_position="last",
    )

    return pd.concat(
        [starts, contains],
        ignore_index=True,
    ).head(limit)


def market_label(player):
    name = player.get(
        "name",
        "Nome desconhecido",
    )

    club = player.get(
        "current_club_name",
        "Clube desconhecido",
    )

    if pd.isna(club):
        club = "Clube desconhecido"

    value = format_market_value(
        player.get(
            "market_value_in_eur",
            None,
        )
    )

    return f"{name} · {club} · {value}"


def get_market_player(
    player_name,
    market_df,
):
    if not player_name or market_df.empty:
        return None

    normalized = normalize_search_text(
        player_name
    )

    matches = market_df[
        market_df["normalized_name"]
        == normalized
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def render_section_title(
    title,
    note=None,
):
    st.markdown(
        f"<div class='gk-section-title'>{title}</div>",
        unsafe_allow_html=True,
    )

    if note:
        st.markdown(
            f"<div class='gk-section-note'>{note}</div>",
            unsafe_allow_html=True,
        )


def render_player_card(
    player,
    market,
    performance=None,
):
    name = (
        performance
        if performance
        else market.get("name", "N/A")
    )

    club = market.get(
        "current_club_name",
        "N/A",
    )

    if pd.isna(club):
        club = "N/A"

    value = format_market_value(
        market.get(
            "market_value_in_eur"
        )
    )

    age = calculate_age(
        market.get(
            "date_of_birth"
        )
    )

    left, middle, right = st.columns(
        [2.2, 1.8, 1]
    )

    with left:
        st.markdown(
            f"<div class='gk-result-name'>🧤 {esc(name)}</div>"
            f"<div class='gk-result-meta'>🏟️ {esc(club)}</div>",
            unsafe_allow_html=True,
        )

    with middle:
        st.markdown(
            f"<div class='gk-kpi-label'>Valor de mercado</div>"
            f"<div class='gk-kpi-value'>{esc(value)}</div>",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f"<div class='gk-kpi-label'>Idade</div>"
            f"<div class='gk-kpi-value'>"
            f"{esc(age)}"
            f"</div>",
            unsafe_allow_html=True,
        )


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(show_spinner="A carregar dados de performance...")
def load_data():
    """
    Lê `gk_performances` (PostgreSQL) e a base de mercado.

    As métricas já vêm materializadas pelo pipeline de ingestão (ver
    `ingest_performances.py`) -- `build_scouting_table()` já NÃO é chamada
    aqui nem em lado nenhum da aplicação. Continua a ser a única fonte de
    cálculo das métricas, mas só dentro do pipeline de ingestão, nunca em
    tempo de pedido da app.

    Devolve duas versões das performances:

    - `table`: uma linha por jogador (a linha com mais minutos, quando
      há várias competições/épocas). É o formato que `similarity_engine`
      já exige (índice único por jogador) -- usado na comparação e nos
      "guarda-redes semelhantes".
    - `performances`: TODAS as linhas, uma por
      (player_name, competition_id, season_id), sem colapsar nada. É o
      que o Player Profile usa para o seletor de contexto (Fase 2).
    """

    performances = load_gk_performances()

    if performances.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )

    # Um jogador pode ter uma linha por (competition_id, season_id).
    # Para `table` (usada por similarity_engine, que exige um índice
    # único por jogador) fica, por jogador, a linha com mais minutos: é
    # a amostra mais fiável disponível, e é uma SELEÇÃO entre linhas já
    # materializadas, nunca um recálculo de métrica nenhuma.
    table = (
        performances
        .sort_values("minutes", ascending=False)
        .drop_duplicates(subset="player_name", keep="first")
        .set_index("player_name")
    )
    table.index.name = "player"

    if "minutes" in table.columns:
        table = table[
            table["minutes"] >= 180
        ].copy()

    market_df = get_goalkeepers()
    market_df = create_name_index(market_df)
    market_df = prepare_market_df(market_df)

    return (
        table,
        performances,
        market_df,
    )


(
    table,
    performances,
    market_df,
) = load_data()


if market_df.empty:
    st.error(
        "Não foi possível carregar a base de mercado."
    )
    st.stop()


# Limiar de minutos sugerido, derivado da amostra realmente carregada.
# Um valor fixo nao serve: o percentil 25 e 286 minutos no Mundial 2022 e
# 190 no dataset multi-competicao.
suggested_min_minutes = default_min_minutes(
    table["minutes"]
    if "minutes" in table.columns
    else []
)


# =========================================================
# MATCH MAP
# =========================================================

@st.cache_data(show_spinner=False)
def build_performance_market_map(
    performance_names,
    _market_df,
):
    """
    `_market_df` leva prefixo `_` de proposito: sinaliza ao Streamlit que
    nao deve tentar gerar hash do DataFrame a cada rerun. E derivado de
    forma deterministica de `load_data()`, por isso `performance_names`
    e suficiente como chave de cache.
    """

    market_df = _market_df

    names = list(performance_names)

    if not names or market_df.empty:
        return {}

    matches = match_players(
        names,
        market_df,
    )

    market_lookup = {
        row["normalized_name"]: row
        for _, row in market_df.iterrows()
    }

    mapping = {}

    for _, row in matches.iterrows():

        statsbomb_name = row.get(
            "statsbomb_name"
        )

        transfermarkt_name = row.get(
            "transfermarkt_name"
        )

        if (
            not statsbomb_name
            or pd.isna(
                transfermarkt_name
            )
        ):
            continue

        normalized = normalize_search_text(
            transfermarkt_name
        )

        market_row = market_lookup.get(
            normalized
        )

        if market_row is not None:
            mapping[
                statsbomb_name
            ] = market_row

    return mapping


# Coberta a partir de TODOS os nomes em `performances`, não só os de
# `table` (que só tem >=180 min, um por jogador) -- estritamente mais
# abrangente, sem alterar `build_performance_market_map`. É o que
# permite ao Discovery mostrar clube/valor mesmo para jogadores com
# amostras pequenas, que `table` deliberadamente exclui.
performance_market_map = (
    build_performance_market_map(
        tuple(performances["player_name"].unique()),
        market_df,
    )
)


def market_for_performance(
    performance_name,
):
    return performance_market_map.get(
        performance_name
    )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="gk-hero">
        <div class="gk-hero-title">🧤 Goalkeeper Scouting</div>
        <div class="gk-hero-subtitle">
            Performance, mercado e análise de perfil de guarda-redes
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# NAVIGATION
# =========================================================

# Navegação programática (Discovery -> Profile, Profile -> Similarity,
# Discovery -> Comparison): o Streamlit não permite escrever em
# st.session_state["main_page"] depois de o widget `st.radio(key="main_page")`
# já ter corrido nesta execução -- por isso os botões que navegam para
# outra página guardam o destino numa chave neutra (`_navigate_to`, sem
# widget associado) e é só aqui, ANTES do radio ser instanciado, que essa
# chave é aplicada a `main_page`.
pending_navigation = st.session_state.pop("_navigate_to", None)
if pending_navigation is not None:
    st.session_state["main_page"] = pending_navigation

page = st.radio(
    "Área",
    [
        "🧭 Discovery",
        "👤 Perfil",
        "⚖️ Comparar",
        "🔎 Encontrar semelhantes",
    ],
    horizontal=True,
    label_visibility="collapsed",
    key="main_page",
)

st.divider()


# =========================================================
# PROFILE / GLOBAL SEARCH
# =========================================================

selected_market_player = None
selected_performance_player = None

if page in (
    "👤 Perfil",
    "⚖️ Comparar",
):

    render_section_title(
        "🔎 Procurar guarda-redes",
        "Escreve pelo menos parte do nome para procurar no mercado.",
    )

    search_query = st.text_input(
        "Pesquisar guarda-redes",
        placeholder=(
            "Ex.: Courtois, Diogo Costa, Donnarumma..."
        ),
        label_visibility="collapsed",
        key="global_search",
    )

    search_results = search_market_players(
        market_df,
        search_query,
        limit=12,
    )

    if not search_query.strip():

        st.info(
            "Pesquisa um guarda-redes para começar."
        )

    elif search_results.empty:

        st.warning(
            "Nenhum guarda-redes encontrado."
        )

    else:

        st.caption(
            f"{len(search_results)} resultado(s)"
        )

        options = [
            (
                market_label(player),
                player["name"],
            )
            for _, player
            in search_results.iterrows()
        ]

        selected_label = st.radio(
            "Resultados",
            [item[0] for item in options],
            horizontal=True,
            label_visibility="collapsed",
            key="global_player",
        )

        selected_market_name = dict(
            options
        ).get(
            selected_label
        )

        selected_market_player = (
            get_market_player(
                selected_market_name,
                market_df,
            )
        )

        if selected_market_name:

            normalized_selected = (
                normalize_search_text(
                    selected_market_name
                )
            )

            for (
                performance_name,
                market_row,
            ) in performance_market_map.items():

                if (
                    normalize_search_text(
                        market_row.get(
                            "name",
                            "",
                        )
                    )
                    == normalized_selected
                ):

                    selected_performance_player = (
                        performance_name
                    )

                    break

    st.divider()


# =========================================================
# PROFILE
# =========================================================

if page == "👤 Perfil":

    # Ligação Discovery -> Player Profile: se o utilizador chegou aqui a
    # partir de um botão "Abrir perfil" no Discovery, esse jogador tem
    # prioridade sobre a pesquisa acima. Usa `.get()`, não `.pop()`: o
    # perfil tem widgets próprios (seletor de contexto, botão de
    # semelhantes) que disparam novas execuções do script, e um `.pop()`
    # perdia a seleção logo na primeira interação. Fica válido até o
    # Discovery definir um novo alvo.
    discovery_target = st.session_state.get("discovery_target_player")

    if discovery_target is not None:
        selected_performance_player = discovery_target
        selected_market_player = market_for_performance(discovery_target)

    if selected_market_player is None:

        st.info(
            "Pesquisa um guarda-redes acima para abrir o perfil."
        )

    else:

        player = selected_market_player

        name = player.get("name", "N/A")

        club = player.get("current_club_name", "N/A")
        if pd.isna(club):
            club = "N/A"

        age = calculate_age(player.get("date_of_birth"))
        value = format_market_value(player.get("market_value_in_eur"))
        highest = format_market_value(player.get("highest_market_value_in_eur"))

        # ---------------------------------------------------------------
        # IDENTIDADE
        # ---------------------------------------------------------------

        st.markdown(
            f"""
            <div class="gk-hero">
                <div class="gk-hero-title">🧤 {esc(name)}</div>
                <div class="gk-hero-subtitle">🧤 Guarda-redes · 🏟️ {esc(club)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("🎂 Idade", f"{age} anos" if age is not None else "N/A")
        c2.metric("💰 Valor de mercado (hoje)", value)
        c3.metric("📈 Maior valor (histórico)", highest)

        st.caption(
            "Idade e valor de mercado refletem a situação atual do "
            "jogador — não a competição/época da performance abaixo."
        )

        st.divider()

        # ---------------------------------------------------------------
        # CONTEXTO DA AMOSTRA + SELETOR (quando há mais de uma linha)
        # ---------------------------------------------------------------

        player_rows = player_context_rows(performances, selected_performance_player)

        if player_rows.empty:

            st.info(
                "Não existem dados de performance StatsBomb "
                "suficientes para este guarda-redes."
            )

        else:

            if len(player_rows) == 1:
                active_row = player_rows.iloc[0]
            else:
                render_section_title(
                    "📅 Competição / época",
                    "Este guarda-redes tem performance registada em mais do "
                    "que uma competição/época. As métricas abaixo mudam "
                    "consoante a seleção — nunca são somadas entre "
                    "contextos diferentes.",
                )

                context_options = {
                    context_label(row): idx
                    for idx, row in player_rows.iterrows()
                }

                chosen_label = st.selectbox(
                    "Contexto da amostra",
                    list(context_options.keys()),
                    label_visibility="collapsed",
                    key="profile_context",
                )

                active_row = player_rows.iloc[context_options[chosen_label]]

            render_section_title("📌 Contexto da amostra")

            c1, c2, c3 = st.columns(3)
            c1.metric("🏆 Competição", f"#{int(active_row['competition_id'])}")
            c2.metric("📅 Época", f"#{int(active_row['season_id'])}")
            c3.metric("⏱️ Minutos", f"{active_row['minutes']:.0f}")

            st.caption(
                "Identificadores de competição/época ainda não têm nome "
                "legível associado nesta fase."
            )

            st.divider()

            # -----------------------------------------------------------
            # SHOT STOPPING
            # -----------------------------------------------------------

            render_section_title("🥅 Shot Stopping")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Save %", format_percentage(active_row["save_pct"]))
            c2.metric("Remates sofridos", format_count(active_row["shots_faced"]))
            c3.metric("Remates defendidos", format_count(active_row["shots_saved"]))
            c4.metric("Golos sofridos", format_count(active_row["goals_conceded"]))

            st.caption(
                f"Remates sofridos por 90 min: "
                f"{format_rate_p90(active_row['shots_faced_p90'])}"
            )

            st.divider()

            # -----------------------------------------------------------
            # SWEEPING
            # -----------------------------------------------------------

            render_section_title(
                "🧤 Sweeping",
                "Ações fora da área. Ausência de ações não é o mesmo que zero.",
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Ações",
                format_count(active_row["sweeper_actions"], empty=NO_ACTIONS_LABEL),
            )
            c2.metric(
                "Ações /90",
                format_rate_p90(active_row["sweeper_actions_p90"], empty=NO_ACTIONS_LABEL),
            )
            c3.metric(
                "Distância média",
                format_distance_m(active_row["avg_distance_from_goal"], empty=NO_ACTIONS_LABEL),
            )
            c4.metric(
                "Distância máxima",
                format_distance_m(active_row["max_distance_from_goal"], empty=NO_ACTIONS_LABEL),
            )

            st.divider()

            # -----------------------------------------------------------
            # DISTRIBUTION
            # -----------------------------------------------------------

            render_section_title("⚽ Distribution")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Passes certos", format_percentage(active_row["pass_success_pct"]))
            c2.metric("Total de passes", format_count(active_row["total_passes"]))
            c3.metric("Comprimento médio", format_distance_m(active_row["avg_pass_length"]))
            c4.metric("Bola longa", format_percentage(active_row["long_ball_pct"]))

            st.divider()

            # -----------------------------------------------------------
            # VISUALIZAÇÕES — radar (reaproveitado) + mapa de saídas
            # -----------------------------------------------------------

            render_section_title("📊 Visualizações")

            radar_col, map_col = st.columns(2)

            with radar_col:
                st.markdown("**Radar de performance**")

                if selected_performance_player in table.index:
                    os.makedirs("output", exist_ok=True)
                    radar_path = "output/_tmp_radar_profile.png"
                    plot_radar(table, [selected_performance_player], radar_path)
                    st.image(radar_path, width="stretch")
                else:
                    st.info("Sem dados suficientes para gerar o radar.")

            with map_col:
                st.markdown("**Mapa de saídas (sweeper)**")
                st.info(
                    "Não disponível nesta fase: o mapa de saídas precisa "
                    "das coordenadas de cada ação individual, que a "
                    "aplicação já não carrega — só lê as métricas "
                    "agregadas em `gk_performances`."
                )

            st.divider()

            # -----------------------------------------------------------
            # SEMELHANTES — ação que navega para a Similarity completa,
            # reaproveitando find_similar_goalkeepers/explain_similarity
            # sem alterações (ver página "🔎 Encontrar semelhantes").
            # -----------------------------------------------------------

            render_section_title(
                "🔎 Guarda-redes semelhantes",
                "Usa este guarda-redes como referência para encontrar "
                "perfis estatisticamente próximos, com pesos ajustáveis.",
            )

            if selected_performance_player not in table.index:

                st.info(
                    "Sem minutos suficientes na amostra para usar este "
                    "guarda-redes como referência de semelhança."
                )

            else:

                if st.button(
                    "🔎 Encontrar guarda-redes semelhantes",
                    key="profile_find_similar",
                ):
                    st.session_state["similarity_target_player"] = (
                        selected_performance_player
                    )
                    st.session_state["_navigate_to"] = "🔎 Encontrar semelhantes"
                    st.rerun()


# =========================================================
# COMPARE
# =========================================================

elif page == "⚖️ Comparar":

    render_section_title(
        "⚖️ Comparar guarda-redes",
        "Compara 2 a 4 guarda-redes — cada um mantém a sua própria "
        "competição/época, nunca misturadas.",
    )

    performance_market_options = [
        (market_label(market), performance_name)
        for performance_name, market in performance_market_map.items()
    ]
    performance_market_options.sort(key=lambda item: item[0])

    labels = [label for label, _ in performance_market_options]
    mapping = dict(performance_market_options)

    # Discovery -> Comparison: se o utilizador veio do botão "Ir para
    # Comparação" no Discovery, pré-seleciona esses jogadores nos
    # widgets abaixo -- tem de acontecer ANTES de os selectbox serem
    # instanciados, por isso fica aqui, não depois.
    comparison_preselect = st.session_state.pop("comparison_preselect", None)

    if comparison_preselect:

        label_by_player = {
            performance_name: label
            for label, performance_name in performance_market_options
        }

        compare_keys = ["compare_1", "compare_2", "compare_3", "compare_4"]

        for key, player_name in zip(compare_keys, comparison_preselect):
            label = label_by_player.get(player_name)
            if label is not None:
                st.session_state[key] = label

    if len(labels) < 2:

        st.warning(
            "São necessários pelo menos dois guarda-redes "
            "com dados de performance."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:
            p1_label = st.selectbox("Guarda-redes 1", labels, key="compare_1")

        with col2:
            p2_label = st.selectbox(
                "Guarda-redes 2",
                labels,
                index=1 if len(labels) > 1 else 0,
                key="compare_2",
            )

        col3, col4 = st.columns(2)

        with col3:
            p3_label = st.selectbox(
                "Guarda-redes 3 (opcional)",
                ["(nenhum)"] + labels,
                key="compare_3",
            )

        with col4:
            p4_label = st.selectbox(
                "Guarda-redes 4 (opcional)",
                ["(nenhum)"] + labels,
                key="compare_4",
            )

        selected_players = [mapping[p1_label], mapping[p2_label]]

        for optional_label in (p3_label, p4_label):
            if optional_label != "(nenhum)":
                selected_players.append(mapping[optional_label])

        if len(set(selected_players)) != len(selected_players):

            st.warning("Escolhe guarda-redes diferentes.")

        else:

            st.divider()

            render_section_title(
                "📅 Contexto de cada jogador",
                "Um jogador com mais do que uma competição/época tem "
                "seletor próprio — as métricas abaixo seguem sempre a "
                "linha escolhida aqui, nunca uma agregação.",
            )

            active_rows = []

            context_cols = st.columns(len(selected_players))

            for col, performance_name in zip(context_cols, selected_players):

                player_rows = player_context_rows(performances, performance_name)

                with col:

                    if player_rows.empty:
                        st.warning(f"Sem dados de performance para {performance_name}.")
                        active_rows.append(None)
                        continue

                    if len(player_rows) == 1:
                        active_row = player_rows.iloc[0]
                    else:
                        context_options = {
                            context_label(row): idx
                            for idx, row in player_rows.iterrows()
                        }
                        chosen_label = st.selectbox(
                            f"Contexto — {performance_name}",
                            list(context_options.keys()),
                            key=f"compare_context_{performance_name}",
                        )
                        active_row = player_rows.iloc[context_options[chosen_label]]

                    active_rows.append(active_row)

                    st.caption(context_label(active_row))

            comparison_table = build_comparison_table(active_rows)

            if comparison_table.empty:

                st.info(
                    "Nenhum dos guarda-redes selecionados tem dados de "
                    "performance suficientes para comparar."
                )

            else:

                st.divider()

                render_section_title("👥 Identidade")

                cards = st.columns(len(selected_players))

                for col, performance_name in zip(cards, selected_players):

                    market = market_for_performance(performance_name)

                    with col:

                        if market is not None:
                            render_player_card(
                                performance_name,
                                market,
                                performance=performance_name,
                            )
                        else:
                            st.markdown(f"**🧤 {esc(performance_name)}**")

                def _metric_group(title, note, rows_spec):
                    st.divider()
                    render_section_title(title, note)

                    table_rows = []

                    for metric, label, formatter, empty in rows_spec:

                        if metric not in comparison_table.columns:
                            continue

                        row = {"Métrica": label}

                        for player_name in comparison_table.index:
                            value = comparison_table.loc[player_name, metric]
                            row[player_name] = formatter(value, empty=empty)

                        table_rows.append(row)

                    st.dataframe(
                        pd.DataFrame(table_rows),
                        width="stretch",
                        hide_index=True,
                    )

                _metric_group(
                    "🥅 Shot Stopping",
                    None,
                    [
                        ("save_pct", "Save %", format_percentage, "N/A"),
                        ("shots_faced", "Remates sofridos", format_count, "N/A"),
                        ("shots_saved", "Remates defendidos", format_count, "N/A"),
                        ("goals_conceded", "Golos sofridos", format_count, "N/A"),
                        ("shots_faced_p90", "Remates sofridos /90", format_rate_p90, "N/A"),
                    ],
                )

                _metric_group(
                    "🧤 Sweeping",
                    "Ausência de ações não é o mesmo que zero.",
                    [
                        ("sweeper_actions", "Ações", format_count, NO_ACTIONS_LABEL),
                        ("sweeper_actions_p90", "Ações /90", format_rate_p90, NO_ACTIONS_LABEL),
                        ("avg_distance_from_goal", "Distância média", format_distance_m, NO_ACTIONS_LABEL),
                        ("max_distance_from_goal", "Distância máxima", format_distance_m, NO_ACTIONS_LABEL),
                    ],
                )

                _metric_group(
                    "⚽ Distribution",
                    None,
                    [
                        ("pass_success_pct", "Passes certos", format_percentage, "N/A"),
                        ("total_passes", "Total de passes", format_count, "N/A"),
                        ("avg_pass_length", "Comprimento médio", format_distance_m, "N/A"),
                        ("long_ball_pct", "Bola longa", format_percentage, "N/A"),
                    ],
                )

                st.divider()
                render_section_title("💰 Market", "Valor atual — não é performance da amostra.")

                market_rows = []
                for label_row, extractor in [
                    ("Clube", lambda m: m.get("current_club_name", "N/A") if m is not None else "N/A"),
                    ("Valor de mercado", lambda m: format_market_value(m.get("market_value_in_eur")) if m is not None else "N/A"),
                    ("Idade (hoje)", lambda m: calculate_age(m.get("date_of_birth")) if m is not None else None),
                ]:
                    row = {"Métrica": label_row}
                    for performance_name in selected_players:
                        market = market_for_performance(performance_name)
                        value = extractor(market)
                        row[performance_name] = "N/A" if value is None or (isinstance(value, float) and pd.isna(value)) else value
                    market_rows.append(row)

                st.dataframe(pd.DataFrame(market_rows), width="stretch", hide_index=True)

                st.button(
                    "🕸️ Gerar radar comparativo",
                    type="primary",
                    key="generate_radar",
                    on_click=None,
                )

                if st.session_state.get("generate_radar", False):

                    with st.spinner("A gerar radar..."):

                        os.makedirs("output", exist_ok=True)
                        path = "output/_tmp_radar_compare.png"

                        plot_radar(
                            comparison_table,
                            list(comparison_table.index),
                            path,
                        )

                        st.image(path, width="stretch")


# =========================================================
# SIMILAR
# =========================================================

elif page == "🔎 Encontrar semelhantes":

    render_section_title(
        "🔎 Encontrar semelhantes",
        "Encontra perfis estatisticamente próximos e filtra por contexto de mercado.",
    )

    # Ligação Player Profile -> Similarity: se o utilizador chegou aqui a
    # partir do botão "Encontrar guarda-redes semelhantes" no perfil, esse
    # jogador é a referência -- salta a pesquisa por nome. Usa `.get()`,
    # não `.pop()`: a página tem sliders de peso e filtros próprios que
    # disparam novas execuções do script, e um `.pop()` perdia a
    # referência logo no primeiro ajuste.
    similarity_target_override = st.session_state.get("similarity_target_player")

    similar_search = st.text_input(
        "Pesquisar guarda-redes de referência",
        placeholder=(
            "Ex.: Donnarumma, Courtois, Diogo Costa..."
        ),
        label_visibility="collapsed",
        key="similar_reference_search",
        disabled=similarity_target_override is not None,
    )

    normalized_similar_search = normalize_search_text(
        similar_search
    )

    if similarity_target_override is None and not normalized_similar_search:

        st.info(
            "Pesquisa pelo nome do guarda-redes que queres usar como referência, "
            "ou usa \"Encontrar guarda-redes semelhantes\" a partir do perfil dele."
        )

    else:

        if similarity_target_override is not None:

            target = similarity_target_override

            st.caption(
                f"🎯 Referência escolhida no Player Profile: **{esc(target)}**"
            )

        else:

            similar_candidates = []

            for performance_name, market in (
                performance_market_map.items()
            ):

                market_name = normalize_search_text(
                    market.get(
                        "name",
                        performance_name,
                    )
                )

                if market_name.startswith(
                    normalized_similar_search
                ):

                    similar_candidates.append(
                        (
                            market_label(market),
                            performance_name,
                            market,
                        )
                    )

            if not similar_candidates:

                for performance_name, market in (
                    performance_market_map.items()
                ):

                    market_name = normalize_search_text(
                        market.get(
                            "name",
                            performance_name,
                        )
                    )

                    if normalized_similar_search in market_name:

                        similar_candidates.append(
                            (
                                market_label(market),
                                performance_name,
                                market,
                            )
                        )

            similar_candidates = sorted(
                similar_candidates,
                key=lambda item: (
                    -float(
                        item[2].get(
                            "market_value_in_eur",
                            0,
                        )
                        or 0
                    )
                ),
            )[:20]

            if not similar_candidates:

                st.warning(
                    "Nenhum guarda-redes encontrado para essa pesquisa."
                )
                target = None

            else:

                st.caption(
                    f"{len(similar_candidates)} resultado(s)"
                )

                similar_labels = [
                    item[0]
                    for item in similar_candidates
                ]

                similar_map = {
                    item[0]: item[1]
                    for item in similar_candidates
                }

                target_label = st.radio(
                    "Resultados",
                    similar_labels,
                    index=0,
                    label_visibility="collapsed",
                    key="similar_reference_result",
                )

                target = similar_map[
                    target_label
                ]

        if target is not None:

            target_market = market_for_performance(
                target
            )

            if target_market is not None:

                club = target_market.get(
                    "current_club_name",
                    "N/A",
                )

                if pd.isna(club):
                    club = "N/A"

                st.markdown(
                    f"""
                    <div class="gk-result">
                        <div class="gk-result-name">
                            🎯 {esc(target)}
                        </div>
                        <div class="gk-result-meta">
                            🏟️ {esc(club)} ·
                            💰 {esc(format_market_value(target_market.get("market_value_in_eur")))} ·
                            🎂 {esc(calculate_age(target_market.get("date_of_birth")))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Contexto usado como referência -- NUNCA escondido: find_similar_
            # goalkeepers opera sempre sobre `table` (a linha de mais minutos
            # de cada jogador), por isso é essa a linha que se mostra aqui.
            target_context = reference_context(table, target)

            if target_context is not None:
                st.caption(
                    "📌 Referência usada no cálculo: "
                    + context_label(target_context)
                    + " (linha com mais minutos deste guarda-redes; "
                    "não muda por si só se o perfil tiver outra selecionada)."
                )
            else:
                st.warning(
                    f"{target} não tem minutos suficientes na amostra "
                    "para ser usado como referência."
                )

            st.divider()

            render_section_title(
                "⚖️ Perfil de scouting",
                "Define quanto cada dimensão deve pesar no perfil final.",
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                w_shot = st.number_input(
                    "🥅 Shot Stopping",
                    min_value=0,
                    max_value=100,
                    value=30,
                    step=5,
                    key="w_shot",
                )

            with c2:
                w_distribution = st.number_input(
                    "⚽ Distribution",
                    min_value=0,
                    max_value=100,
                    value=35,
                    step=5,
                    key="w_distribution",
                )

            with c3:
                w_proactivity = st.number_input(
                    "🧤 Proactivity",
                    min_value=0,
                    max_value=100,
                    value=35,
                    step=5,
                    key="w_proactivity",
                )

            total = (
                w_shot
                + w_distribution
                + w_proactivity
            )

            # Os pesos sao sempre normalizados pela soma, por isso o que
            # conta e a proporcao entre dimensoes. Em vez de fingir que a
            # soma tem de dar 100, mostramos a proporcao efetivamente usada.
            if total <= 0:

                st.warning(
                    "Define pelo menos uma dimensão com peso maior que zero."
                )

            else:

                effective = normalise_dimension_weights(
                    {
                        "Shot Stopping": w_shot,
                        "Distribution": w_distribution,
                        "Proactivity": w_proactivity,
                    }
                )

                st.caption(
                    "Peso efetivamente aplicado: "
                    f"🥅 Shot Stopping {effective['Shot Stopping']:.0%} · "
                    f"⚽ Distribution {effective['Distribution']:.0%} · "
                    f"🧤 Proactivity {effective['Proactivity']:.0%}"
                )

            st.divider()

            render_section_title(
                "🎛️ Filtros"
            )

            c1, c2, c3, c4, c5 = st.columns(5)

            with c1:
                max_market_value = st.number_input(
                    "💰 Valor máximo (€M)",
                    min_value=0.0,
                    max_value=500.0,
                    value=50.0,
                    step=5.0,
                    help="0 = sem limite",
                    key="similar_max_market",
                )

            with c2:
                max_age = st.number_input(
                    "🎂 Idade máxima",
                    min_value=16,
                    max_value=45,
                    value=35,
                    step=1,
                    help="0 = sem limite",
                    key="similar_max_age",
                )

            with c3:
                min_similarity = st.number_input(
                    "🎯 Similaridade mínima (%)",
                    min_value=0,
                    max_value=100,
                    value=60,
                    step=5,
                    key="similar_minimum",
                )

            with c4:
                min_minutes = st.number_input(
                    "⏱️ Minutos mínimos",
                    min_value=90,
                    max_value=5000,
                    value=suggested_min_minutes,
                    step=90,
                    help=(
                        "Sugerido a partir da amostra carregada "
                        "(percentil 25, arredondado a jogos completos)."
                    ),
                    key="similar_minutes",
                )

            with c5:
                top_n = st.number_input(
                    "👥 Candidatos",
                    min_value=3,
                    max_value=20,
                    value=5,
                    step=1,
                    key="similar_top_n",
                )

            st.caption(
                "Valor máximo ou idade máxima = 0 significa sem limite."
            )

            run_similarity = st.button(
                "🔎 Procurar semelhantes",
                type="primary",
                disabled=(total <= 0),
                key="run_similarity",
            )

            if run_similarity:

                weights = {
                    "Shot Stopping": w_shot,
                    "Distribution": w_distribution,
                    "Proactivity": w_proactivity,
                }

                calculation_top_n = min(
                    max(
                        int(top_n) * 10,
                        50,
                    ),
                    500,
                )

                with st.spinner(
                    "A calcular perfis semelhantes..."
                ):

                    try:

                        sim = find_similar_goalkeepers(
                            table,
                            target,
                            top_n=calculation_top_n,
                            features=STYLE_FEATURES,
                            min_minutes=int(min_minutes),
                            dimension_weights=weights,
                        )

                    except Exception as exc:

                        st.error(
                            f"Não foi possível calcular os semelhantes: {exc}"
                        )

                        sim = pd.DataFrame()

                # Market filter
                if (
                    not sim.empty
                    and max_market_value > 0
                ):

                    max_value_eur = (
                        float(max_market_value)
                        * 1_000_000
                    )

                    allowed = []

                    for candidate in sim.index:

                        market = market_for_performance(
                            candidate
                        )

                        if market is None:
                            allowed.append(candidate)
                            continue

                        value = pd.to_numeric(
                            market.get(
                                "market_value_in_eur"
                            ),
                            errors="coerce",
                        )

                        if (
                            pd.isna(value)
                            or float(value) <= max_value_eur
                        ):

                            allowed.append(candidate)

                    sim = sim.loc[
                        sim.index.isin(
                            allowed
                        )
                    ].copy()

                # Age filter
                if (
                    not sim.empty
                    and int(max_age) > 0
                ):

                    allowed = []

                    for candidate in sim.index:

                        market = market_for_performance(
                            candidate
                        )

                        if market is None:
                            allowed.append(candidate)
                            continue

                        age = calculate_age(
                            market.get(
                                "date_of_birth"
                            )
                        )

                        if (
                            age is None
                            or age <= int(max_age)
                        ):
                            allowed.append(candidate)

                    sim = sim.loc[
                        sim.index.isin(
                            allowed
                        )
                    ].copy()

                # Minimum similarity
                if not sim.empty:

                    sim = sim[
                        sim["similarity_pct"]
                        >= float(
                            min_similarity
                        )
                    ].copy()

                if not sim.empty:
                    sim = sim.head(
                        int(top_n)
                    )

                st.divider()

                render_section_title(
                    "🎯 Resultados",
                    f"Perfis que cumprem os filtros definidos.",
                )

                if sim.empty:

                    st.info(
                        "Nenhum candidato atingiu todos os filtros selecionados."
                    )

                else:

                    # Uma única montagem, reutilizada na tabela e na leitura
                    # de scouting -- evita calcular o contexto/mercado de
                    # cada candidato duas vezes. Não reordena nem filtra
                    # `sim` de novo: usa exatamente o que find_similar_
                    # goalkeepers() devolveu, na mesma ordem.
                    similarity_rows = build_similarity_rows(
                        sim,
                        table,
                        target,
                        performance_market_map,
                        explain_similarity,
                        STYLE_FEATURES,
                    )

                    table_rows = []

                    for entry in similarity_rows:

                        table_rows.append(
                            {
                                "#": entry["rank"],
                                "Guarda-redes": entry["player_name"],
                                "Competição": (
                                    f"#{entry['competition_id']}"
                                    if entry["competition_id"] is not None
                                    else "N/A"
                                ),
                                "Época": (
                                    f"#{entry['season_id']}"
                                    if entry["season_id"] is not None
                                    else "N/A"
                                ),
                                "Minutos": format_count(entry["minutes"]),
                                "Clube": (
                                    entry["current_club_name"]
                                    if entry["current_club_name"]
                                    else "N/A"
                                ),
                                "Valor de mercado": format_market_value(
                                    entry["market_value_in_eur"]
                                ),
                                "Similaridade (%)": round(entry["similarity_pct"], 1),
                            }
                        )

                    st.dataframe(
                        pd.DataFrame(table_rows),
                        width="stretch",
                        hide_index=True,
                    )

                    render_section_title(
                        "🧠 Leitura de scouting"
                    )

                    for entry in similarity_rows:

                        meta = ""

                        if entry["current_club_name"]:
                            meta = (
                                f" · {entry['current_club_name']} · "
                                f"{format_market_value(entry['market_value_in_eur'])}"
                            )

                        context = (
                            f" · #{entry['competition_id']}/#{entry['season_id']}"
                            if entry["competition_id"] is not None
                            else ""
                        )

                        st.markdown(
                            f"**{entry['rank']}. {esc(entry['player_name'])}** — "
                            f"{entry['similarity_pct']:.1f}% de similaridade"
                            f"{context}{meta}"
                        )

                        st.caption(entry["explanation"])


# =========================================================
# DISCOVERY
# =========================================================
#
# Dois modos claramente separados (pedido explícito): pesquisa por nome
# e descoberta por filtros. Nenhum dos dois recalcula métricas -- ambos
# trabalham sobre `performances`, já materializada de gk_performances.
#
# Filtro de "estilo" (proatividade/conservador): NÃO implementado.
# similarity_engine.py expõe uma dimensão "Proactivity" (sweeper_actions_p90
# + avg_distance_from_goal), mas combinar essas duas colunas num único
# filtro/slider seria inventar um score de estilo pela porta do lado --
# exatamente o que este projeto já rejeitou explicitamente ao desenhar
# o motor de similaridade com pesos por dimensão em vez de uma métrica
# única. Um filtro de um só eixo (ex.: só avg_distance_from_goal) também
# excluiria silenciosamente todos os guarda-redes com essa métrica a NaN
# (quem nunca saiu da baliza -- ver M5/S3). Fica de fora desta fase.

elif page == "🧭 Discovery":

    render_section_title(
        "🧭 Discovery",
        "Descobre guarda-redes por nome ou por perfil de filtros.",
    )

    discovery_mode = st.radio(
        "Modo",
        [
            "🔎 Pesquisar por nome",
            "🎯 Descobrir por filtros",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="discovery_mode",
    )

    st.caption(
        "🔎 Pesquisar por nome"
        if discovery_mode == "🔎 Pesquisar por nome"
        else "🎯 A procurar candidatos com um determinado perfil, não um jogador específico."
    )

    st.divider()

    st.session_state.setdefault("discovery_compare_selection", [])

    def _render_discovery_results(results):

        if results.empty:
            st.info("Nenhum guarda-redes encontrado com estes critérios.")
            return

        st.caption(f"{len(results)} resultado(s)")

        selection = st.session_state["discovery_compare_selection"]

        for i, row in results.iterrows():

            with st.container(border=True):

                left, right = st.columns([3, 1])

                with left:

                    club = row.get("current_club_name")
                    club_text = "N/A" if club is None or pd.isna(club) else club

                    st.markdown(
                        f"**🧤 {esc(row['player_name'])}** · 🏟️ {esc(club_text)}"
                    )

                    st.caption(
                        f"🏆 Competição #{int(row['competition_id'])} · "
                        f"📅 Época #{int(row['season_id'])} · "
                        f"⏱️ {row['minutes']:.0f} min"
                    )

                    m1, m2, m3 = st.columns(3)
                    m1.metric(
                        "Valor de mercado",
                        format_market_value(row.get("market_value_in_eur")),
                    )
                    m2.metric(
                        "Save %",
                        format_percentage(row.get("save_pct")),
                    )
                    m3.metric(
                        "Idade",
                        format_count(row.get("age")),
                    )

                with right:

                    row_key = (
                        f"{i}_{row['player_name']}_"
                        f"{row['competition_id']}_{row['season_id']}"
                    )

                    if st.button("🧤 Abrir perfil", key=f"discovery_open_{row_key}"):
                        st.session_state["discovery_target_player"] = row["player_name"]
                        st.session_state["_navigate_to"] = "👤 Perfil"
                        st.rerun()

                    player_name = row["player_name"]
                    is_selected = player_name in selection

                    wants_compare = st.checkbox(
                        "⚖️ Comparar",
                        value=is_selected,
                        key=f"discovery_compare_{row_key}",
                    )

                    if wants_compare and not is_selected:
                        if len(selection) < 4:
                            selection.append(player_name)
                        else:
                            st.warning("Já tens 4 guarda-redes selecionados.")
                    elif not wants_compare and is_selected:
                        selection.remove(player_name)

    if discovery_mode == "🔎 Pesquisar por nome":

        name_query = st.text_input(
            "Pesquisar guarda-redes",
            placeholder="Ex.: Diogo Costa, Courtois, Donnarumma...",
            label_visibility="collapsed",
            key="discovery_name_search",
        )

        if not name_query.strip():
            st.info("Escreve pelo menos parte do nome para pesquisar.")
        else:
            matches = search_by_name(performances, name_query)
            enriched = enrich_with_market(matches, performance_market_map)
            _render_discovery_results(enriched)

    else:

        render_section_title("🎯 Filtros")

        competitions = available_competitions(performances)
        competition_options = ["Todas as competições"] + [
            f"#{competition_id}" for competition_id in competitions
        ]

        c1, c2 = st.columns(2)

        with c1:
            competition_choice = st.selectbox(
                "Competição",
                competition_options,
                key="discovery_competition",
            )

        selected_competition_id = (
            None
            if competition_choice == "Todas as competições"
            else int(competition_choice.lstrip("#"))
        )

        seasons = available_seasons(performances, selected_competition_id)
        season_options = ["Todas as épocas"] + [
            f"#{season_id}" for season_id in seasons
        ]

        with c2:
            season_choice = st.selectbox(
                "Época",
                season_options,
                key="discovery_season",
            )

        selected_season_id = (
            None
            if season_choice == "Todas as épocas"
            else int(season_choice.lstrip("#"))
        )

        c3, c4, c5 = st.columns(3)

        with c3:
            min_minutes_filter = st.number_input(
                "Minutos mínimos",
                min_value=0,
                max_value=5000,
                value=int(default_min_minutes(performances["minutes"])),
                step=90,
                help="0 = sem limite",
                key="discovery_min_minutes",
            )

        with c4:
            max_age_filter = st.number_input(
                "Idade máxima",
                min_value=0,
                max_value=45,
                value=0,
                step=1,
                help="0 = sem limite",
                key="discovery_max_age",
            )

        with c5:
            max_value_filter = st.number_input(
                "Valor máximo (€M)",
                min_value=0.0,
                max_value=500.0,
                value=0.0,
                step=5.0,
                help="0 = sem limite",
                key="discovery_max_value",
            )

        st.caption("Qualquer filtro a 0 significa sem limite nesse critério.")

        run_discovery = st.button(
            "🎯 Procurar candidatos",
            type="primary",
            key="discovery_run",
        )

        if run_discovery:

            enriched = enrich_with_market(performances, performance_market_map)

            candidates = filter_candidates(
                enriched,
                competition_id=selected_competition_id,
                season_id=selected_season_id,
                min_minutes=(
                    float(min_minutes_filter) if min_minutes_filter > 0 else None
                ),
                max_age=(
                    float(max_age_filter) if max_age_filter > 0 else None
                ),
                max_market_value=(
                    float(max_value_filter) * 1_000_000
                    if max_value_filter > 0
                    else None
                ),
            )

            # st.button só é True na execução imediatamente a seguir ao
            # clique -- marcar "Comparar" num resultado dispara uma nova
            # execução em que run_discovery já voltou a False, e os
            # resultados desapareciam. Guardar em session_state faz os
            # resultados sobreviverem a essas interações seguintes, sem
            # precisar de carregar outra vez em "Procurar candidatos".
            st.session_state["discovery_filter_results"] = candidates

        if "discovery_filter_results" in st.session_state:
            st.divider()
            render_section_title("🎯 Resultados")
            _render_discovery_results(st.session_state["discovery_filter_results"])

    # ---------------------------------------------------------------
    # Discovery -> Comparison: mesma técnica (session_state + rerun)
    # já usada para Discovery -> Profile.
    # ---------------------------------------------------------------

    compare_selection = st.session_state.get("discovery_compare_selection", [])

    if compare_selection:

        st.divider()

        st.markdown(
            f"**⚖️ Selecionados para comparar ({len(compare_selection)}/4):** "
            + ", ".join(esc(name) for name in compare_selection)
        )

        if len(compare_selection) >= 2:

            if st.button(
                "⚖️ Ir para Comparação",
                type="primary",
                key="discovery_go_compare",
            ):
                st.session_state["comparison_preselect"] = list(compare_selection)
                st.session_state["discovery_compare_selection"] = []
                st.session_state["_navigate_to"] = "⚖️ Comparar"
                st.rerun()

        else:

            st.caption("Seleciona pelo menos 2 para poderes comparar.")