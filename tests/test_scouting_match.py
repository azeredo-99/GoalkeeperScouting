"""
Testes de `gk_scouting.scouting_match` -- o motor de Scouting Match.

Cobrem especificamente as garantias arquiteturais pedidas:
- dados em falta != mau desempenho ("insufficient_data" nunca conta
  como "unmet", nunca reduz o match_score);
- mesmo jogador + perfil diferente = resultado diferente;
- mesmo jogador + mesmo perfil + contexto diferente = resultado
  potencialmente diferente (o contexto está implícito nos valores
  passados, nunca combinado);
- valores fronteira (== minimum / == maximum contam como matched);
- a função é pura e não sabe nada sobre outros jogadores/perfis
  (testável isolada, sem BD nem API).
"""

from gk_scouting.scouting_match import match_player_to_profile
from gk_scouting.scouting_profiles import Preference, ScoutingProfile, get_profile


def _profile(*prefs: Preference) -> ScoutingProfile:
    return ScoutingProfile(id="test", name="Test", description="", preferences={p.metric: p for p in prefs})


def _player(**kwargs):
    base = {
        "save_pct": None,
        "sweeper_actions_p90": None,
        "avg_distance_from_goal": None,
        "pass_success_pct": None,
        "long_ball_pct": None,
        "age": None,
        "market_value_eur": None,
        "minutes": None,
    }
    base.update(kwargs)
    return base


# ===========================================================================
# status básico: matched / unmet / insufficient_data
# ===========================================================================

def test_value_within_range_is_matched():
    profile = _profile(Preference("save_pct", enabled=True, minimum=70.0))
    result = match_player_to_profile(_player(save_pct=80.0), profile)
    assert result.evaluations[0].status == "matched"
    assert result.matched_count == 1
    assert result.unmet_count == 0
    assert result.insufficient_count == 0


def test_value_below_minimum_is_unmet():
    profile = _profile(Preference("save_pct", enabled=True, minimum=70.0))
    result = match_player_to_profile(_player(save_pct=50.0), profile)
    assert result.evaluations[0].status == "unmet"
    assert result.unmet_count == 1


def test_value_above_maximum_is_unmet():
    profile = _profile(Preference("long_ball_pct", enabled=True, maximum=25.0))
    result = match_player_to_profile(_player(long_ball_pct=40.0), profile)
    assert result.evaluations[0].status == "unmet"


def test_missing_value_is_insufficient_data_never_unmet():
    """Regra crítica: dados em falta não é mau desempenho."""
    profile = _profile(Preference("long_ball_pct", enabled=True, maximum=25.0))
    result = match_player_to_profile(_player(long_ball_pct=None), profile)
    assert result.evaluations[0].status == "insufficient_data"
    assert result.unmet_count == 0
    assert result.insufficient_count == 1


def test_disabled_preferences_are_not_evaluated():
    profile = _profile(
        Preference("save_pct", enabled=True, minimum=70.0),
        Preference("age", enabled=False, maximum=23.0),
    )
    result = match_player_to_profile(_player(save_pct=80.0, age=35.0), profile)
    assert len(result.evaluations) == 1
    assert result.evaluations[0].metric == "save_pct"


# ===========================================================================
# valores fronteira
# ===========================================================================

def test_value_exactly_at_minimum_is_matched():
    profile = _profile(Preference("save_pct", enabled=True, minimum=70.0))
    result = match_player_to_profile(_player(save_pct=70.0), profile)
    assert result.evaluations[0].status == "matched"


def test_value_exactly_at_maximum_is_matched():
    profile = _profile(Preference("age", enabled=True, maximum=23.0))
    result = match_player_to_profile(_player(age=23.0), profile)
    assert result.evaluations[0].status == "matched"


def test_value_just_below_minimum_is_unmet():
    profile = _profile(Preference("save_pct", enabled=True, minimum=70.0))
    result = match_player_to_profile(_player(save_pct=69.99), profile)
    assert result.evaluations[0].status == "unmet"


def test_preference_without_minimum_or_maximum_always_matches_when_present():
    """Um lado em aberto (ou ambos) significa 'sem limite nesse sentido'."""
    profile = _profile(Preference("save_pct", enabled=True))
    result = match_player_to_profile(_player(save_pct=1.0), profile)
    assert result.evaluations[0].status == "matched"


# ===========================================================================
# match_score -- explicável, nunca penaliza dados em falta
# ===========================================================================

def test_match_score_is_none_when_no_enabled_preference_has_data():
    profile = _profile(Preference("save_pct", enabled=True, minimum=70.0))
    result = match_player_to_profile(_player(save_pct=None), profile)
    assert result.match_score is None


def test_match_score_ignores_insufficient_data_in_denominator():
    """
    Duas preferências com peso igual: uma matched, uma sem dados. O
    score tem de refletir 100% do que foi possível avaliar, não 50%
    penalizado pela ausência de dados.
    """
    profile = _profile(
        Preference("save_pct", enabled=True, weight=1.0, minimum=70.0),
        Preference("long_ball_pct", enabled=True, weight=1.0, maximum=25.0),
    )
    result = match_player_to_profile(_player(save_pct=80.0, long_ball_pct=None), profile)
    assert result.match_score == 100.0
    assert result.insufficient_count == 1


def test_match_score_reflects_weighted_ratio():
    profile = _profile(
        Preference("save_pct", enabled=True, weight=3.0, minimum=70.0),  # matched
        Preference("long_ball_pct", enabled=True, weight=1.0, maximum=25.0),  # unmet
    )
    result = match_player_to_profile(_player(save_pct=80.0, long_ball_pct=40.0), profile)
    # matched_weight (3) / evaluated_weight (3+1=4) * 100 = 75.0
    assert result.match_score == 75.0


# ===========================================================================
# separação PLAYER × PROFILE × CONTEXT
# ===========================================================================

def test_same_player_different_profile_gives_different_result():
    player = _player(save_pct=80.0, sweeper_actions_p90=0.1, age=35.0)

    sweeper_profile = _profile(Preference("sweeper_actions_p90", enabled=True, weight=1.0, minimum=1.0))
    young_profile = _profile(Preference("age", enabled=True, weight=1.0, maximum=23.0))

    sweeper_result = match_player_to_profile(player, sweeper_profile)
    young_result = match_player_to_profile(player, young_profile)

    assert sweeper_result.evaluations[0].status == "unmet"  # 0.1 < 1.0
    assert young_result.evaluations[0].status == "unmet"  # 35 > 23
    # Perfis diferentes = avaliações completamente distintas, nunca o
    # mesmo "score do jogador" reaproveitado.
    assert sweeper_result.evaluations[0].metric != young_result.evaluations[0].metric


def test_same_player_same_profile_different_context_can_differ():
    """
    O 'jogador' aqui já representa um contexto específico (quem chama
    esta função escolhe os valores) -- dois contextos do mesmo jogador
    são dois dicts diferentes, nunca combinados.
    """
    profile = _profile(Preference("save_pct", enabled=True, minimum=70.0))

    context_a = _player(save_pct=80.0)  # ex.: UEFA Euro 2024
    context_b = _player(save_pct=50.0)  # ex.: FIFA World Cup 2022

    result_a = match_player_to_profile(context_a, profile)
    result_b = match_player_to_profile(context_b, profile)

    assert result_a.evaluations[0].status == "matched"
    assert result_b.evaluations[0].status == "unmet"


def test_function_is_pure_and_profile_independent_of_player_data():
    """A mesma instância de perfil pode avaliar jogadores diferentes sem estado partilhado."""
    profile = _profile(Preference("save_pct", enabled=True, minimum=70.0))
    result_1 = match_player_to_profile(_player(save_pct=90.0), profile)
    result_2 = match_player_to_profile(_player(save_pct=10.0), profile)
    assert result_1.evaluations[0].status == "matched"
    assert result_2.evaluations[0].status == "unmet"
    # O objeto `profile` não foi alterado entre as duas chamadas.
    assert profile.preferences["save_pct"].minimum == 70.0


# ===========================================================================
# perfis reais (integração leve com scouting_profiles.py)
# ===========================================================================

def test_high_line_sweeper_profile_matches_a_proactive_keeper():
    profile = get_profile("high-line-sweeper")
    player = _player(
        sweeper_actions_p90=1.5,
        avg_distance_from_goal=18.0,
        pass_success_pct=85.0,
        save_pct=70.0,
        minutes=600.0,
    )
    result = match_player_to_profile(player, profile)
    assert result.unmet_count == 0
    assert result.insufficient_count == 0
    assert result.match_score == 100.0


def test_young_prospect_profile_flags_an_older_keeper_as_unmet():
    profile = get_profile("young-prospect")
    player = _player(age=35.0, minutes=900.0, save_pct=75.0)
    result = match_player_to_profile(player, profile)
    age_eval = next(e for e in result.evaluations if e.metric == "age")
    assert age_eval.status == "unmet"
