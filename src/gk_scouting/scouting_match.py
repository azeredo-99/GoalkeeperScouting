"""
Scouting Match -- "quão bem este guarda-redes encaixa nas preferências
deste Scouting Profile?"

Isto NÃO é Similarity. Similarity (`similarity_engine.py`, inalterado)
responde "que jogadores se parecem estatisticamente com este". Scouting
Match responde "que jogadores correspondem ao que estou a procurar" --
um conceito de scouting diferente, deliberadamente separado.

Princípio arquitetural (não negociável): um match é sempre
PLAYER × PROFILE × CONTEXT. Nunca um "score do jogador" armazenado ou
calculado independentemente de perfil e de amostra. A mesma chamada
com o mesmo jogador mas perfil ou contexto diferentes pode (e deve
poder) dar um resultado diferente.

Puro, sem I/O -- recebe os valores já calculados por metrics.py (via a
camada de apresentação existente), nunca os recalcula.
"""

from dataclasses import dataclass

from .scouting_profiles import PREFERENCE_METRICS, ScoutingProfile


@dataclass(frozen=True)
class PreferenceEvaluation:
    """
    Avaliação de uma preferência para um jogador específico.

    `status` é sempre um destes três, nunca um quarto valor inventado:
    - "matched": o valor existe e satisfaz o intervalo [minimum, maximum].
    - "unmet": o valor existe mas está fora do intervalo.
    - "insufficient_data": o jogador não tem valor para esta métrica
      neste contexto -- NUNCA tratado como "unmet" (ausência de dados
      não é mau desempenho).
    """

    metric: str
    label: str
    status: str
    value: float | None
    minimum: float | None
    maximum: float | None
    weight: float


@dataclass(frozen=True)
class ScoutingMatchResult:
    profile_id: str
    profile_name: str
    evaluations: tuple[PreferenceEvaluation, ...]
    matched_count: int
    unmet_count: int
    insufficient_count: int
    # Fração ponderada de preferências satisfeitas, calculada SÓ sobre as
    # preferências com dados (nunca penaliza dados em falta). `None`
    # quando nenhuma preferência ativada tem dados -- não existe base
    # para calcular nada, por isso não se inventa um número.
    # Secundário e explicável por construção (soma de pesos correspondidos
    # a dividir pela soma de pesos avaliáveis) -- nunca um "rating".
    match_score: float | None
    evaluated_weight: float
    total_weight: float


def match_player_to_profile(player, profile: ScoutingProfile) -> ScoutingMatchResult:
    """
    Avalia `player` (um dict/Series com as chaves de
    `scouting_profiles.PREFERENCE_METRICS` -- save_pct,
    sweeper_actions_p90, avg_distance_from_goal, pass_success_pct,
    long_ball_pct, age, market_value_eur, minutes) contra as
    preferências ativadas de `profile`.

    `context` (competition/season/minutes) já está implícito em
    `player`: quem chama esta função é responsável por passar os
    valores do CONTEXTO CERTO (nunca uma média entre seasons) -- esta
    função não sabe nem precisa de saber de onde vieram.
    """
    evaluations: list[PreferenceEvaluation] = []
    matched = unmet = insufficient = 0
    evaluated_weight = 0.0
    total_weight = 0.0

    for pref in profile.enabled_preferences():
        total_weight += pref.weight
        raw = player.get(pref.metric) if hasattr(player, "get") else getattr(player, pref.metric, None)
        value = None if raw is None else float(raw)

        if value is None:
            status = "insufficient_data"
            insufficient += 1
        else:
            within_min = pref.minimum is None or value >= pref.minimum
            within_max = pref.maximum is None or value <= pref.maximum
            if within_min and within_max:
                status = "matched"
                matched += 1
            else:
                status = "unmet"
                unmet += 1
            evaluated_weight += pref.weight

        evaluations.append(
            PreferenceEvaluation(
                metric=pref.metric,
                label=PREFERENCE_METRICS[pref.metric],
                status=status,
                value=value,
                minimum=pref.minimum,
                maximum=pref.maximum,
                weight=pref.weight,
            )
        )

    if evaluated_weight > 0:
        matched_weight = sum(e.weight for e in evaluations if e.status == "matched")
        match_score = round((matched_weight / evaluated_weight) * 100, 1)
    else:
        match_score = None

    return ScoutingMatchResult(
        profile_id=profile.id,
        profile_name=profile.name,
        evaluations=tuple(evaluations),
        matched_count=matched,
        unmet_count=unmet,
        insufficient_count=insufficient,
        match_score=match_score,
        evaluated_weight=evaluated_weight,
        total_weight=total_weight,
    )
