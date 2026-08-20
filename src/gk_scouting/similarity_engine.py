"""
Goalkeeper Scouting — motor de similaridade.

Versão otimizada e orientada a scouting:
- cálculo totalmente vetorizado;
- pesos por dimensão;
- 100% apenas quando todas as métricas usadas são iguais;
- minutos apenas como filtro de elegibilidade;
- explicação dos candidatos sem recalcular o universo inteiro.
"""

import numpy as np
import pandas as pd


STYLE_FEATURES = [
    "sweeper_actions_p90",
    "avg_distance_from_goal",
    "save_pct",
    "pass_success_pct",
    "avg_pass_length",
    "long_ball_pct",
]


DIMENSION_FEATURES = {
    "Shot Stopping": [
        "save_pct",
    ],
    "Distribution": [
        "pass_success_pct",
        "avg_pass_length",
        "long_ball_pct",
    ],
    "Proactivity": [
        "sweeper_actions_p90",
        "avg_distance_from_goal",
    ],
}


# Um jogo completo. Serve de unidade para arredondar limiares de minutos,
# para os defaults cairem em numeros que um scout le como "N jogos".
MATCH_MINUTES = 90

# Limiar minimo absoluto quando a amostra nao permite calcular um percentil.
MIN_MINUTES_FLOOR = 90


def default_min_minutes(minutes) -> int:
    """
    Escolhe um limiar de minutos a partir da distribuicao real da amostra.

    Regra: percentil 25 arredondado para baixo ao multiplo de 90.

    Porque o percentil 25: mantem cerca de tres quartos da amostra elegivel,
    o que garante que a funcionalidade apresenta candidatos na primeira
    utilizacao, sem deixar entrar guarda-redes com amostras minusculas.
    Porque arredondado a 90: um limiar de "270 minutos" le-se como tres
    jogos; "286 minutos" nao se le como nada.

    Um valor fixo nao serve porque as amostras diferem muito entre datasets:
    no Mundial 2022 o percentil 25 e 286 minutos, no dataset multi-competicao
    e 190. Um default de 720 (o valor anterior) deixava 2 dos 41
    guarda-redes do Mundial elegiveis.
    """

    values = pd.to_numeric(
        pd.Series(minutes),
        errors="coerce",
    ).dropna()

    if values.empty:
        return MIN_MINUTES_FLOOR

    p25 = float(
        values.quantile(0.25)
    )

    floored = int(
        p25 // MATCH_MINUTES * MATCH_MINUTES
    )

    return max(
        MIN_MINUTES_FLOOR,
        floored,
    )


FEATURE_LABELS = {
    "sweeper_actions_p90": "proatividade a sair da baliza",
    "avg_distance_from_goal": "distância média da baliza",
    "save_pct": "eficácia de defesas",
    "pass_success_pct": "eficácia de passe",
    "avg_pass_length": "comprimento médio de passe",
    "long_ball_pct": "tendência para bola longa",
}


def _available_features(table, features):
    result = []

    for feature in features:
        if feature not in table.columns:
            continue

        values = pd.to_numeric(
            table[feature],
            errors="coerce",
        )

        if values.notna().sum() >= 2:
            result.append(feature)

    return result


def _robust_zscore(table, features):
    """
    Calcula robust z-score por coluna.

    Retorna uma tabela com as mesmas linhas e apenas as features pedidas.
    """
    values = (
        table[features]
        .apply(pd.to_numeric, errors="coerce")
        .astype(float)
    )

    median = values.median()
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    # Fallback para colunas com IQR=0.
    std = values.std(ddof=0)

    scale = iqr * 0.7413
    scale = scale.where(
        scale.abs() > 1e-12,
        std,
    )
    scale = scale.where(
        scale.abs() > 1e-12,
        1.0,
    )

    return (
        values
        .sub(median, axis="columns")
        .div(scale, axis="columns")
    )


DEFAULT_DIMENSION_WEIGHTS = {
    "Shot Stopping": 30.0,
    "Distribution": 35.0,
    "Proactivity": 35.0,
}


def normalise_dimension_weights(dimension_weights=None):
    """
    Converte pesos em bruto na proporcao efetivamente usada no calculo.

    Os pesos sao sempre divididos pela soma, por isso 30/35/35 e 10/10/10
    NAO sao equivalentes -- mas 30/35/35 e 60/70/70 sao. O que conta e a
    proporcao entre dimensoes, nunca o valor absoluto nem quanto falta
    para 100. Esta funcao e publica precisamente para a interface poder
    mostrar ao utilizador a proporcao real em vez do que ele escreveu.

    Devolve um dicionario cujos valores somam 1.0.

    Erros:
        ValueError se algum peso for negativo, ou se a soma for zero
        (nesse caso nao existe qualquer dimensao para comparar).
    """

    source = (
        DEFAULT_DIMENSION_WEIGHTS
        if dimension_weights is None
        else dimension_weights
    )

    values = {}

    for dimension in DIMENSION_FEATURES:
        try:
            value = float(
                source.get(dimension, 0)
            )
        except (TypeError, ValueError):
            value = 0.0

        if value < 0:
            raise ValueError(
                f"O peso de '{dimension}' nao pode ser negativo "
                f"(recebido: {value})."
            )

        values[dimension] = value

    total = sum(values.values())

    if total <= 0:
        raise ValueError(
            "A soma dos pesos tem de ser superior a 0."
        )

    return {
        key: value / total
        for key, value in values.items()
    }


def _effective_feature_weights(
    available_features,
    dimension_weights=None,
):
    dimensions = normalise_dimension_weights(
        dimension_weights
    )

    feature_weights = {}

    for dimension, dimension_weight in dimensions.items():
        features = [
            feature
            for feature in DIMENSION_FEATURES[dimension]
            if feature in available_features
        ]

        if not features:
            continue

        share = dimension_weight / len(features)

        for feature in features:
            feature_weights[feature] = share

    total = sum(feature_weights.values())

    if total <= 0:
        raise ValueError(
            "Não existem métricas suficientes para calcular a similaridade."
        )

    return {
        feature: weight / total
        for feature, weight in feature_weights.items()
    }


def _similarity_matrix(
    z,
    target_player,
    feature_weights,
):
    """
    Calcula todas as similaridades em NumPy de uma vez.

    score = weighted mean(exp(-1.15 * abs(delta)))
    """
    features = list(feature_weights.keys())

    matrix = z[features].to_numpy(dtype=float)
    target = z.loc[
        target_player,
        features,
    ].to_numpy(dtype=float)

    weights = np.array(
        [
            feature_weights[feature]
            for feature in features
        ],
        dtype=float,
    )

    delta = np.abs(
        matrix - target
    )

    feature_similarity = np.exp(
        -1.15 * delta
    )

    scores = (
        feature_similarity
        @ weights
    )

    return scores


def find_similar_goalkeepers(
    table: pd.DataFrame,
    target_player: str,
    top_n: int = 5,
    features=None,
    min_minutes: int = 180,
    dimension_weights=None,
) -> pd.DataFrame:
    """
    Encontra os guarda-redes mais semelhantes ao alvo.

    O cálculo é executado apenas quando esta função é chamada,
    e todas as comparações são vetorizadas.
    """

    if table is None or table.empty:
        return pd.DataFrame()

    if target_player not in table.index:
        raise ValueError(
            f"'{target_player}' não existe na tabela de performance."
        )

    if "minutes" not in table.columns:
        raise ValueError(
            "A tabela não contém 'minutes'."
        )

    requested = list(
        features or STYLE_FEATURES
    )

    requested = [
        feature
        for feature in requested
        if feature in STYLE_FEATURES
    ]

    available = _available_features(
        table,
        requested,
    )

    if not available:
        raise ValueError(
            "Não existem métricas suficientes."
        )

    minutes = pd.to_numeric(
        table["minutes"],
        errors="coerce",
    )

    pool = table.loc[
        minutes >= min_minutes
    ].copy()

    pool = pool.dropna(
        subset=available
    )

    if target_player not in pool.index:
        raise ValueError(
            f"'{target_player}' não tem pelo menos "
            f"{min_minutes} minutos com dados completos."
        )

    if len(pool) <= 1:
        return pd.DataFrame()

    z = _robust_zscore(
        pool,
        available,
    )

    weights = _effective_feature_weights(
        available,
        dimension_weights,
    )

    scores = _similarity_matrix(
        z,
        target_player,
        weights,
    )

    scores = pd.Series(
        scores,
        index=z.index,
        name="similarity_pct",
    )

    scores = scores.drop(
        labels=[target_player],
        errors="ignore",
    )

    result = (
        scores
        .sort_values(
            ascending=False,
        )
        .head(
            int(top_n)
        )
        .to_frame()
    )

    result["similarity_pct"] = (
        result["similarity_pct"] * 100
    )

    result["similarity"] = (
        result["similarity_pct"] / 100
    )

    context = [
        feature
        for feature in STYLE_FEATURES
        if feature in pool.columns
    ]

    result = result.join(
        pool[
            context + ["minutes"]
        ]
    )

    order = [
        "similarity_pct",
        "similarity",
        "minutes",
        *context,
    ]

    return result[
        list(
            dict.fromkeys(
                [
                    column
                    for column in order
                    if column in result.columns
                ]
            )
        )
    ]


def explain_similarity(
    table: pd.DataFrame,
    target_player: str,
    candidate: str,
    features=None,
) -> str:
    """Explica rapidamente a proximidade e a maior diferença."""

    features = [
        feature
        for feature in (
            features or STYLE_FEATURES
        )
        if feature in table.columns
    ]

    if (
        target_player not in table.index
        or candidate not in table.index
    ):
        return "Dados insuficientes para explicar este candidato."

    pair = table.loc[
        [target_player, candidate],
        features,
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    valid = [
        feature
        for feature in features
        if pair[feature].notna().all()
    ]

    if not valid:
        return "Dados insuficientes para explicar este candidato."

    z = _robust_zscore(
        table,
        valid,
    )

    differences = (
        z.loc[
            candidate,
            valid,
        ]
        - z.loc[
            target_player,
            valid,
        ]
    ).abs()

    closest = differences.idxmin()
    furthest = differences.idxmax()

    if differences[furthest] < 0.25:
        return (
            f"{candidate} apresenta um perfil muito próximo de "
            f"{target_player}, com diferenças reduzidas nas métricas analisadas."
        )

    target_value = z.loc[
        target_player,
        furthest,
    ]
    candidate_value = z.loc[
        candidate,
        furthest,
    ]

    direction = (
        "acima"
        if candidate_value > target_value
        else "abaixo"
    )

    return (
        f"{candidate} é mais semelhante a {target_player} em "
        f"{FEATURE_LABELS.get(closest, closest)}, "
        f"mas está {direction} do perfil de referência em "
        f"{FEATURE_LABELS.get(furthest, furthest)}."
    )