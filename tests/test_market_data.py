"""
Testes de `gk_scouting.market_data.calculate_age` e
`season_reference_date` -- o bug real que motivou isto: a idade era
sempre calculada a partir de hoje, nunca da época do desempenho
mostrado, o que é sempre errado neste projeto (todos os dados são de
épocas passadas).
"""

import pandas as pd
import pytest

from gk_scouting.market_data import calculate_age, season_reference_date


# --- season_reference_date -------------------------------------------------

def test_season_reference_date_two_year_season_uses_ending_year():
    assert season_reference_date("2015/2016") == pd.Timestamp(2016, 7, 1)


def test_season_reference_date_single_year_season():
    assert season_reference_date("2018") == pd.Timestamp(2018, 7, 1)


def test_season_reference_date_rejects_unparseable_name():
    with pytest.raises(ValueError):
        season_reference_date("no year here")


def test_season_reference_date_rejects_empty_name():
    with pytest.raises(ValueError):
        season_reference_date("")


# --- calculate_age -----------------------------------------------------------

def test_calculate_age_uses_as_of_not_today():
    # Nascido em 1990-06-15: em 2016-07-01 já fez 26 anos.
    age = calculate_age("1990-06-15", as_of=pd.Timestamp(2016, 7, 1))
    assert age == 26


def test_calculate_age_before_birthday_in_reference_year():
    # Nascido em 1990-08-15: em 2016-07-01 ainda não fez anos nesse ano.
    age = calculate_age("1990-08-15", as_of=pd.Timestamp(2016, 7, 1))
    assert age == 25


def test_calculate_age_different_reference_dates_give_different_ages():
    """
    O mesmo nascimento, duas épocas diferentes, tem de dar idades
    diferentes -- é exatamente isto que faltava antes da correção (a
    idade era sempre a mesma, calculada a partir de hoje).
    """
    dob = "1994-01-01"
    age_2016 = calculate_age(dob, as_of=season_reference_date("2015/2016"))
    age_2023 = calculate_age(dob, as_of=season_reference_date("2022/2023"))
    assert age_2016 == 22
    assert age_2023 == 29
    assert age_2016 != age_2023


def test_calculate_age_without_as_of_falls_back_to_today():
    age = calculate_age("2000-01-01")
    assert age == pd.Timestamp.today().year - 2000 - (
        (pd.Timestamp.today().month, pd.Timestamp.today().day) < (1, 1)
    )


def test_calculate_age_missing_date_of_birth_returns_none():
    assert calculate_age(None) is None
    assert calculate_age(float("nan")) is None


def test_calculate_age_invalid_date_returns_none_not_error():
    assert calculate_age("not a date", as_of=pd.Timestamp(2016, 7, 1)) is None
