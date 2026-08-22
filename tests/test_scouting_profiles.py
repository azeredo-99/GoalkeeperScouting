"""
Testes de `gk_scouting.scouting_profiles` -- criação e validação do
modelo de Scouting Profile. Não testam matching (ver
test_scouting_match.py) nem UI.
"""

import pytest

from gk_scouting.scouting_profiles import (
    DEFAULT_PROFILES,
    PROFILE_REGISTRY,
    Preference,
    ScoutingProfile,
    get_profile,
)


def test_preference_rejects_unknown_metric():
    with pytest.raises(ValueError):
        Preference("not_a_real_metric", enabled=True)


def test_preference_rejects_negative_weight():
    with pytest.raises(ValueError):
        Preference("save_pct", enabled=True, weight=-1.0)


def test_preference_rejects_minimum_above_maximum():
    with pytest.raises(ValueError):
        Preference("save_pct", enabled=True, minimum=80.0, maximum=50.0)


def test_preference_allows_minimum_equal_maximum():
    pref = Preference("save_pct", enabled=True, minimum=70.0, maximum=70.0)
    assert pref.minimum == pref.maximum == 70.0


def test_preference_defaults_are_disabled():
    pref = Preference("save_pct")
    assert pref.enabled is False


def test_scouting_profile_enabled_preferences_excludes_disabled():
    profile = ScoutingProfile(
        id="test",
        name="Test profile",
        description="",
        preferences={
            "save_pct": Preference("save_pct", enabled=True),
            "age": Preference("age", enabled=False),
        },
    )
    enabled = profile.enabled_preferences()
    assert len(enabled) == 1
    assert enabled[0].metric == "save_pct"


# --- three example profiles exist and are well-formed ---

def test_three_default_profiles_exist():
    assert len(DEFAULT_PROFILES) == 3
    ids = {p.id for p in DEFAULT_PROFILES}
    assert ids == {"high-line-sweeper", "possession-goalkeeper", "young-prospect"}


def test_default_profiles_have_at_least_one_enabled_preference():
    for profile in DEFAULT_PROFILES:
        assert len(profile.enabled_preferences()) > 0, f"{profile.id} has no enabled preferences"


def test_get_profile_returns_none_for_unknown_id():
    assert get_profile("does-not-exist") is None


def test_get_profile_returns_registered_profile():
    profile = get_profile("high-line-sweeper")
    assert profile is not None
    assert profile.name == "High-Line Sweeper"


def test_profile_registry_matches_default_profiles():
    assert set(PROFILE_REGISTRY.keys()) == {p.id for p in DEFAULT_PROFILES}
