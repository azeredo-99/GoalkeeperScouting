"""
Scouting Profiles -- modelo de dados para "o que este scout procura".

Um Scouting Profile NÃO é uma classificação objetiva do jogador. É uma
predefinição de scouting: um conjunto de preferências (métrica + peso +
mínimo/máximo opcionais) que o scout define. `scouting_match.py` usa
este modelo para avaliar UM jogador × UM contexto contra UM perfil --
nunca o inverso, nunca um "score do jogador" independente de perfil.

Puro, sem I/O, sem dependência de FastAPI/pandas -- testável isolado.
"""

import json
from dataclasses import dataclass, field


# Chaves de preferência válidas -- todas already existentes no produto:
# as 5 métricas de performance (mesmas colunas de gk_performances) mais
# idade, valor de mercado e minutos (já disponíveis via a API existente,
# nenhuma métrica nova).
PREFERENCE_METRICS = {
    "save_pct": "Save %",
    "sweeper_actions_p90": "Sweeper actions /90",
    "avg_distance_from_goal": "Average distance from goal",
    "pass_success_pct": "Pass success %",
    "long_ball_pct": "Long ball %",
    "age": "Age",
    "market_value_eur": "Market value",
    "minutes": "Minutes",
}


@dataclass(frozen=True)
class Preference:
    """
    Uma preferência do scout sobre uma métrica.

    `enabled=False` significa que esta métrica não faz parte do perfil
    (ignorada na avaliação, não "falhada"). `minimum`/`maximum` são
    ambos opcionais -- um lado em aberto significa "sem limite nesse
    sentido", nunca um valor escondido por omissão.
    """

    metric: str
    enabled: bool = False
    weight: float = 1.0
    minimum: float | None = None
    maximum: float | None = None

    def __post_init__(self):
        if self.metric not in PREFERENCE_METRICS:
            raise ValueError(f"Métrica de preferência desconhecida: '{self.metric}'")
        if self.weight < 0:
            raise ValueError(f"O peso de '{self.metric}' não pode ser negativo (recebido: {self.weight}).")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError(
                f"'{self.metric}': minimum ({self.minimum}) não pode ser maior que maximum ({self.maximum})."
            )


@dataclass(frozen=True)
class ScoutingProfile:
    """
    Uma predefinição de scouting -- "o que estou a procurar", não "quão
    bom é este jogador". `preferences` é indexado por chave de métrica.
    """

    id: str
    name: str
    description: str
    preferences: dict[str, Preference] = field(default_factory=dict)

    def enabled_preferences(self) -> list[Preference]:
        return [p for p in self.preferences.values() if p.enabled]


def _profile(profile_id: str, name: str, description: str, *prefs: Preference) -> ScoutingProfile:
    return ScoutingProfile(
        id=profile_id,
        name=name,
        description=description,
        preferences={p.metric: p for p in prefs},
    )


# Três perfis de exemplo -- predefinições de scouting, não classificações
# objetivas. Os valores de minimum/maximum são limiares de exemplo
# razoáveis para o domínio (percentagens, metros, anos, minutos, euros),
# não derivados de nenhuma população real -- o scout pode ajustá-los.
HIGH_LINE_SWEEPER = _profile(
    "high-line-sweeper",
    "High-Line Sweeper",
    "Goalkeeper suited to a high defensive line and possession-oriented team.",
    Preference("sweeper_actions_p90", enabled=True, weight=3.0, minimum=1.0),
    Preference("avg_distance_from_goal", enabled=True, weight=2.5, minimum=15.0),
    Preference("pass_success_pct", enabled=True, weight=1.5, minimum=75.0),
    Preference("save_pct", enabled=True, weight=1.0, minimum=60.0),
    Preference("long_ball_pct", enabled=False),
    Preference("minutes", enabled=True, weight=0.5, minimum=270.0),
)

POSSESSION_GOALKEEPER = _profile(
    "possession-goalkeeper",
    "Possession Goalkeeper",
    "Comfortable building play from the back with short, reliable distribution.",
    Preference("pass_success_pct", enabled=True, weight=3.0, minimum=80.0),
    Preference("long_ball_pct", enabled=True, weight=2.0, maximum=25.0),
    Preference("save_pct", enabled=True, weight=1.0, minimum=60.0),
    Preference("sweeper_actions_p90", enabled=False),
    Preference("minutes", enabled=True, weight=0.5, minimum=270.0),
)

YOUNG_PROSPECT = _profile(
    "young-prospect",
    "Young Prospect",
    "Younger goalkeeper with a workable sample and room to develop.",
    Preference("age", enabled=True, weight=2.5, maximum=23.0),
    Preference("minutes", enabled=True, weight=1.5, minimum=180.0),
    Preference("save_pct", enabled=True, weight=1.0, minimum=55.0),
    Preference("market_value_eur", enabled=False),
)

DEFAULT_PROFILES: list[ScoutingProfile] = [HIGH_LINE_SWEEPER, POSSESSION_GOALKEEPER, YOUNG_PROSPECT]
PROFILE_REGISTRY: dict[str, ScoutingProfile] = {p.id: p for p in DEFAULT_PROFILES}


def get_profile(profile_id: str) -> ScoutingProfile | None:
    return PROFILE_REGISTRY.get(profile_id)


def parse_custom_profile(raw: str) -> ScoutingProfile:
    """
    Constrói um ScoutingProfile a partir da definição enviada inline pelo
    frontend (mesma forma que `_profile_dict()` em main.py produz) --
    um perfil que o scout criou/editou no browser e que nunca é
    persistido no servidor (ver customScoutingProfiles.ts no frontend:
    localStorage é a fonte da verdade). O backend só o vê por pedido,
    tal como reavalia os predefinidos a cada pedido -- nenhum estado
    novo, nenhuma tabela nova.

    Reaproveita inteiramente a validação já existente em
    Preference/ScoutingProfile (metrica desconhecida, peso negativo,
    minimum > maximum) -- não duplica regras.

    Levanta ValueError em qualquer entrada inválida ou vazia de
    critérios úteis. Quem chamar isto (a API) tem de transformar isso
    num erro explícito para o utilizador -- nunca num perfil "vazio"
    aplicado silenciosamente.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Custom profile is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Custom profile must be a JSON object.")

    raw_preferences = data.get("preferences")
    if not isinstance(raw_preferences, list) or not raw_preferences:
        raise ValueError("Custom profile must include a non-empty 'preferences' list.")

    preferences: list[Preference] = []
    for entry in raw_preferences:
        if not isinstance(entry, dict) or "metric" not in entry:
            raise ValueError("Each preference must be an object with a 'metric'.")
        try:
            preferences.append(
                Preference(
                    metric=entry["metric"],
                    enabled=bool(entry.get("enabled", False)),
                    weight=float(entry.get("weight", 1.0)),
                    minimum=None if entry.get("minimum") is None else float(entry["minimum"]),
                    maximum=None if entry.get("maximum") is None else float(entry["maximum"]),
                )
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid preference for '{entry.get('metric')}': {exc}") from exc

    profile = ScoutingProfile(
        id=str(data.get("id") or "custom"),
        name=str(data.get("name") or "Custom profile"),
        description=str(data.get("description") or ""),
        preferences={p.metric: p for p in preferences},
    )

    if not profile.enabled_preferences():
        raise ValueError("Custom profile has no enabled preferences -- enable at least one before matching.")

    return profile
