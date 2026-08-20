import os
import urllib.request
import urllib.error

import pandas as pd


# =========================================================
# CONFIGURAÇÃO
# =========================================================

TRANSFERMARKT_URL = (
    "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/"
    "data/players.csv.gz"
)

# Ficheiro local onde guardamos a base depois do primeiro download
LOCAL_DATA_DIR = "data"
LOCAL_PLAYERS_FILE = os.path.join(
    LOCAL_DATA_DIR,
    "transfermarkt_players.csv.gz",
)

# Timeout máximo para tentar obter os dados externos
DOWNLOAD_TIMEOUT = 30


# =========================================================
# DOWNLOAD
# =========================================================

def download_transfermarkt_players():
    """
    Descarrega a base Transfermarkt uma única vez.

    Depois de descarregada, a aplicação passa a utilizar
    exclusivamente a cópia local.
    """

    os.makedirs(
        LOCAL_DATA_DIR,
        exist_ok=True,
    )

    print(
        "A descarregar base Transfermarkt..."
    )

    try:

        request = urllib.request.Request(
            TRANSFERMARKT_URL,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/151.0 Safari/537.36"
                )
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=DOWNLOAD_TIMEOUT,
        ) as response:

            with open(
                LOCAL_PLAYERS_FILE,
                "wb",
            ) as file:

                while True:

                    chunk = response.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    file.write(chunk)

        print(
            "Base Transfermarkt descarregada com sucesso."
        )

        return True

    except Exception as error:

        print(
            f"Erro ao descarregar Transfermarkt: {error}"
        )

        return False


# =========================================================
# CARREGAR BASE
# =========================================================

def load_transfermarkt_players():
    """
    Carrega a base de jogadores.

    Prioridade:

    1. Ficheiro local
    2. Download da fonte Transfermarkt

    A aplicação não faz download sempre que arranca.
    """

    # -----------------------------------------------------
    # BASE LOCAL
    # -----------------------------------------------------

    if os.path.exists(
        LOCAL_PLAYERS_FILE
    ):

        print(
            "A carregar base Transfermarkt local..."
        )

        try:

            players = pd.read_csv(
                LOCAL_PLAYERS_FILE,
                compression="gzip",
            )

            print(
                f"Base carregada: {len(players):,} jogadores."
            )

            return players

        except Exception as error:

            print(
                f"Erro a ler base local: {error}"
            )

            print(
                "A tentar novo download..."
            )

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    success = download_transfermarkt_players()

    if not success:

        return pd.DataFrame()

    # -----------------------------------------------------
    # LER FICHEIRO DESCARREGADO
    # -----------------------------------------------------

    try:

        players = pd.read_csv(
            LOCAL_PLAYERS_FILE,
            compression="gzip",
        )

        print(
            f"Base carregada: {len(players):,} jogadores."
        )

        return players

    except Exception as error:

        print(
            f"Erro ao ler base descarregada: {error}"
        )

        return pd.DataFrame()


# =========================================================
# GUARDA-REDES
# =========================================================

def get_goalkeepers():
    """
    Devolve apenas guarda-redes.

    A informação é carregada da cópia local da base
    Transfermarkt sempre que possível.
    """

    players = load_transfermarkt_players()

    if players.empty:

        return pd.DataFrame()

    # Garantir que a coluna existe
    if "position" not in players.columns:

        print(
            "Erro: coluna 'position' não encontrada."
        )

        return pd.DataFrame()

    # Normalizar posição
    positions = (
        players["position"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    goalkeepers = players[
        positions == "goalkeeper"
    ].copy()

    # -----------------------------------------------------
    # Garantir colunas necessárias
    # -----------------------------------------------------

    required_columns = [
        "player_id",
        "name",
        "date_of_birth",
        "position",
        "current_club_name",
        "market_value_in_eur",
        "highest_market_value_in_eur",
    ]

    for column in required_columns:

        if column not in goalkeepers.columns:

            goalkeepers[column] = None

    goalkeepers = goalkeepers[
        required_columns
    ]

    # -----------------------------------------------------
    # Valor de mercado
    # -----------------------------------------------------

    goalkeepers[
        "market_value_in_eur"
    ] = pd.to_numeric(
        goalkeepers[
            "market_value_in_eur"
        ],
        errors="coerce",
    )

    goalkeepers[
        "highest_market_value_in_eur"
    ] = pd.to_numeric(
        goalkeepers[
            "highest_market_value_in_eur"
        ],
        errors="coerce",
    )

    # -----------------------------------------------------
    # Ordenar pelos mais valiosos
    # -----------------------------------------------------

    goalkeepers = (
        goalkeepers
        .sort_values(
            "market_value_in_eur",
            ascending=False,
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    print(
        f"Guarda-redes encontrados: "
        f"{len(goalkeepers):,}"
    )

    return goalkeepers


# =========================================================
# VALOR DE MERCADO
# =========================================================

def format_market_value(value):
    """
    Formata valores de mercado.

    Exemplos:

        50000000 -> €50.0M
        12500000 -> €12.5M
        500000   -> €500K
        75000    -> €75K
    """

    if pd.isna(value):

        return "N/A"

    try:

        value = float(value)

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"

    if value >= 1_000_000:

        return (
            f"€{value / 1_000_000:.1f}M"
        )

    if value >= 1_000:

        return (
            f"€{value / 1_000:.0f}K"
        )

    return (
        f"€{value:.0f}"
    )


# =========================================================
# IDADE
# =========================================================

def calculate_age(date_of_birth):
    """
    Calcula a idade atual.
    """

    if pd.isna(date_of_birth):

        return None

    try:

        birth_date = pd.to_datetime(
            date_of_birth
        )

        today = pd.Timestamp.today()

        age = (
            today.year
            - birth_date.year
            - (
                (today.month, today.day)
                < (
                    birth_date.month,
                    birth_date.day,
                )
            )
        )

        return age

    except Exception:

        return None