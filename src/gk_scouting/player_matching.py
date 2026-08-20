import re
import unicodedata
from typing import Iterable

import pandas as pd


# =========================================================
# NORMALIZAÇÃO
# =========================================================

def normalize_name(name: str) -> str:
    """Normaliza um nome para matching rápido e consistente."""

    if pd.isna(name):
        return ""

    name = str(name).lower().strip()

    name = unicodedata.normalize(
        "NFKD",
        name,
    )

    name = "".join(
        char
        for char in name
        if not unicodedata.combining(char)
    )

    # Mantemos apenas letras/números/espaços.
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def name_tokens(name: str) -> tuple[str, ...]:
    """Devolve os tokens de um nome normalizado."""

    normalized = normalize_name(name)

    if not normalized:
        return ()

    return tuple(normalized.split())


# =========================================================
# ÍNDICES
# =========================================================

def create_name_index(
    transfermarkt_players: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepara a base Transfermarkt para matching.

    Além das colunas de compatibilidade já usadas pelo projeto,
    cria:
        - first_name
        - last_name
    """

    df = transfermarkt_players.copy()

    if "name" not in df.columns:
        raise ValueError(
            "A base Transfermarkt tem de conter a coluna 'name'."
        )

    normalized = (
        df["name"]
        .fillna("")
        .astype(str)
        .map(normalize_name)
    )

    df["normalized_name"] = normalized
    df["name_tokens"] = normalized.map(
        lambda value: tuple(value.split()) if value else ()
    )

    df["first_name"] = normalized.map(
        lambda value: value.split()[0] if value else ""
    )

    df["last_name"] = normalized.map(
        lambda value: value.split()[-1] if value else ""
    )

    return df


def _build_indexes(
    transfermarkt_players: pd.DataFrame,
):
    """
    Cria índices O(1) para exact, first+last e tokens.

    Os índices são mantidos em dicionários Python leves.
    """

    if (
        "normalized_name" not in transfermarkt_players.columns
        or "name_tokens" not in transfermarkt_players.columns
        or "first_name" not in transfermarkt_players.columns
        or "last_name" not in transfermarkt_players.columns
    ):
        transfermarkt_players = create_name_index(
            transfermarkt_players
        )

    exact_index: dict[str, list] = {}
    first_last_index: dict[tuple[str, str], list] = {}
    token_index: dict[str, list] = {}

    for idx, row in transfermarkt_players[
        [
            "normalized_name",
            "name_tokens",
            "first_name",
            "last_name",
        ]
    ].iterrows():

        normalized = row["normalized_name"]

        if normalized:
            exact_index.setdefault(
                normalized,
                [],
            ).append(idx)

        first = row["first_name"]
        last = row["last_name"]

        if first and last:
            first_last_index.setdefault(
                (first, last),
                [],
            ).append(idx)

        for token in set(row["name_tokens"]):
            if len(token) >= 3:
                token_index.setdefault(
                    token,
                    [],
                ).append(idx)

    return (
        transfermarkt_players,
        exact_index,
        first_last_index,
        token_index,
    )


# =========================================================
# MATCH INDIVIDUAL
# =========================================================

def _unique_row(
    players: pd.DataFrame,
    indices: Iterable,
):
    indices = list(dict.fromkeys(indices))

    if len(indices) != 1:
        return None

    return players.loc[indices[0]]


def match_player(
    statsbomb_name: str,
    transfermarkt_players: pd.DataFrame,
):
    """
    Faz matching sem percorrer a BD inteira.

    Ordem:
        1. exact name
        2. first + last
        3. token subset
        4. first + last entre candidatos de token
    """

    if pd.isna(statsbomb_name):
        return None

    normalized = normalize_name(
        statsbomb_name
    )

    if not normalized:
        return None

    (
        players,
        exact_index,
        first_last_index,
        token_index,
    ) = _build_indexes(
        transfermarkt_players
    )

    # -----------------------------------------------------
    # 1. EXACT
    # -----------------------------------------------------

    exact = _unique_row(
        players,
        exact_index.get(
            normalized,
            [],
        ),
    )

    if exact is not None:
        return exact

    tokens = tuple(
        normalized.split()
    )

    if len(tokens) < 2:
        return None

    first = tokens[0]
    last = tokens[-1]

    # -----------------------------------------------------
    # 2. FIRST + LAST
    # -----------------------------------------------------

    first_last = _unique_row(
        players,
        first_last_index.get(
            (first, last),
            [],
        ),
    )

    if first_last is not None:
        return first_last

    # -----------------------------------------------------
    # 3/4. TOKEN CANDIDATES
    # -----------------------------------------------------

    candidate_indices = set()

    for token in set(tokens):
        if len(token) < 3:
            continue

        candidate_indices.update(
            token_index.get(
                token,
                [],
            )
        )

    if not candidate_indices:
        return None

    # Primeiro tentar os candidatos cujo conjunto TM
    # está contido no conjunto StatsBomb.
    stats_tokens = set(tokens)
    subset_matches = []

    for idx in candidate_indices:

        tm_tokens = set(
            players.at[idx, "name_tokens"]
        )

        if (
            len(tm_tokens) >= 2
            and tm_tokens.issubset(stats_tokens)
        ):
            subset_matches.append(idx)

    result = _unique_row(
        players,
        subset_matches,
    )

    if result is not None:
        return result

    # Última tentativa: first + last entre candidatos.
    first_last_candidates = []

    for idx in candidate_indices:

        if (
            players.at[idx, "first_name"] == first
            and players.at[idx, "last_name"] == last
        ):
            first_last_candidates.append(idx)

    return _unique_row(
        players,
        first_last_candidates,
    )


# =========================================================
# MATCH MULTIPLE
# =========================================================

def _match_many(
    statsbomb_players,
    transfermarkt_players: pd.DataFrame,
):
    """
    Matching em lote reutilizando os índices uma única vez.
    """

    players, exact_index, first_last_index, token_index = (
        _build_indexes(
            transfermarkt_players
        )
    )

    rows = []

    for player in sorted(
        {
            value
            for value in statsbomb_players
            if not pd.isna(value)
        }
    ):

        normalized = normalize_name(
            player
        )

        match = None

        if normalized:

            # 1. Exact
            match = _unique_row(
                players,
                exact_index.get(
                    normalized,
                    [],
                ),
            )

            if match is None:

                tokens = tuple(
                    normalized.split()
                )

                if len(tokens) >= 2:

                    first = tokens[0]
                    last = tokens[-1]

                    # 2. First + last
                    match = _unique_row(
                        players,
                        first_last_index.get(
                            (first, last),
                            [],
                        ),
                    )

                    # 3. Token candidates
                    if match is None:

                        candidate_indices = set()

                        for token in set(tokens):

                            if len(token) >= 3:

                                candidate_indices.update(
                                    token_index.get(
                                        token,
                                        [],
                                    )
                                )

                        stats_tokens = set(tokens)
                        subset_matches = []

                        for idx in candidate_indices:

                            tm_tokens = set(
                                players.at[
                                    idx,
                                    "name_tokens",
                                ]
                            )

                            if (
                                len(tm_tokens) >= 2
                                and tm_tokens.issubset(
                                    stats_tokens
                                )
                            ):
                                subset_matches.append(
                                    idx
                                )

                        match = _unique_row(
                            players,
                            subset_matches,
                        )

                        # 4. First + last among candidates
                        if match is None:

                            first_last_candidates = [
                                idx
                                for idx
                                in candidate_indices
                                if (
                                    players.at[
                                        idx,
                                        "first_name",
                                    ]
                                    == first
                                    and
                                    players.at[
                                        idx,
                                        "last_name",
                                    ]
                                    == last
                                )
                            ]

                            match = _unique_row(
                                players,
                                first_last_candidates,
                            )

        if match is None:

            rows.append(
                {
                    "statsbomb_name": player,
                    "transfermarkt_name": None,
                    "player_id": None,
                    "date_of_birth": None,
                    "current_club_name": None,
                    "market_value_in_eur": None,
                    "highest_market_value_in_eur": None,
                    "match_status": "not_found",
                }
            )

        else:

            rows.append(
                {
                    "statsbomb_name": player,
                    "transfermarkt_name": match.get(
                        "name"
                    ),
                    "player_id": match.get(
                        "player_id"
                    ),
                    "date_of_birth": match.get(
                        "date_of_birth"
                    ),
                    "current_club_name": match.get(
                        "current_club_name"
                    ),
                    "market_value_in_eur": match.get(
                        "market_value_in_eur"
                    ),
                    "highest_market_value_in_eur": match.get(
                        "highest_market_value_in_eur"
                    ),
                    "match_status": "matched",
                }
            )

    return pd.DataFrame(rows)


def match_players(
    statsbomb_players,
    transfermarkt_players: pd.DataFrame,
) -> pd.DataFrame:
    """Faz matching em lote de vários jogadores."""

    return _match_many(
        statsbomb_players,
        transfermarkt_players,
    )


def enrich_scouting_table(
    scouting_table: pd.DataFrame,
    transfermarkt_players: pd.DataFrame,
) -> pd.DataFrame:
    """Junta métricas StatsBomb com dados Transfermarkt."""

    market = _match_many(
        scouting_table.index,
        transfermarkt_players,
    ).set_index(
        "statsbomb_name"
    )

    return scouting_table.join(
        market,
        how="left",
    )