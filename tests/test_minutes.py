"""
Testes do cálculo de minutos baseado em `Starting XI` + substituições (P0-2).

Os cenários são construídos com os helpers de `conftest.py`, que reproduzem
a estrutura real do StatsBomb. O último teste do ficheiro valida a
interpretação contra um jogo real do dataset.
"""

import os

import numpy as np
import pandas as pd
import pytest

from conftest import EVENT_COLUMNS, filler, gk_event, gk_pass, starting_xi, substitution
from gk_scouting.data_loader import build_gk_events
from gk_scouting.metrics import (
    PERIOD_ENDS,
    compute_minutes_played,
    goalkeeper_minutes_by_match,
    match_regulation_duration,
    matches_without_lineup,
    regulation_minute,
    starting_lineups,
)


def events_from(rows):
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


def minutes_for(rows):
    events = events_from(rows)
    return goalkeeper_minutes_by_match(events, build_gk_events(events))


def minutes_of(rows, player, match_id=1):
    frame = minutes_for(rows)
    row = frame[(frame["player"] == player) & (frame["match_id"] == match_id)]
    if row.empty:
        return None
    return float(row["minutes"].iloc[0])


# ---------------------------------------------------------------------------
# Relógio regulamentar
# ---------------------------------------------------------------------------

def test_regulation_minute_within_regulation_is_unchanged():
    assert regulation_minute(1, 19) == 19.0
    assert regulation_minute(2, 79) == 79.0
    assert regulation_minute(4, 110) == 110.0


def test_regulation_minute_absorbs_stoppage_time():
    """
    O relógio de evento corre pela compensação adentro (verificado: o período
    1 chega ao minuto 59 e o período 2 ao 103). Uma substituição aos 95' do
    período 2 conta como tendo acontecido aos 90'.
    """
    assert regulation_minute(1, 59) == 45.0
    assert regulation_minute(2, 103) == 90.0
    assert regulation_minute(4, 124) == 120.0


def test_regulation_minute_clamps_to_the_period_start():
    """O período 2 começa aos 45; nenhum evento seu conta como anterior."""
    assert regulation_minute(2, 45) == 45.0
    assert regulation_minute(3, 90) == 90.0


def test_regulation_minute_rejects_the_shootout_period():
    with pytest.raises(ValueError, match="nao corresponde a tempo de jogo"):
        regulation_minute(5, 125)


# ---------------------------------------------------------------------------
# Cenários pedidos
# ---------------------------------------------------------------------------

def test_1_starter_who_plays_the_whole_match_gets_ninety():
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        filler(1, 2, 90),
    ]
    assert minutes_of(rows, "Keeper") == 90.0


def test_2_starter_substituted_at_sixty_gets_sixty():
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        substitution(1, 2, 60, "Team X", "Keeper", "Backup"),
        gk_event(1, 2, 70, "Backup", "Team X", "Shot Faced"),
        filler(1, 2, 90),
    ]
    assert minutes_of(rows, "Keeper") == 60.0


def test_3_substitute_who_comes_on_at_sixty_gets_thirty():
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        substitution(1, 2, 60, "Team X", "Keeper", "Backup"),
        gk_event(1, 2, 70, "Backup", "Team X", "Shot Faced"),
        filler(1, 2, 90),
    ]
    assert minutes_of(rows, "Backup") == 30.0


def test_4_bench_keeper_who_never_comes_on_is_excluded():
    """
    Um guarda-redes que fica no banco não está no `Starting XI` nem tem
    substituição de entrada. Não recebe minutos e não aparece de todo.
    """
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        # O suplente aquece e é registado num evento, mas nunca entra.
        gk_event(1, 1, 50, "Bench Keeper", "Team X", "Shot Faced"),
        filler(1, 2, 90),
    ]
    frame = minutes_for(rows)
    assert "Bench Keeper" not in set(frame["player"])
    assert minutes_of(rows, "Keeper") == 90.0


def test_5_extra_time_without_substitution_gives_one_hundred_and_twenty():
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        filler(1, 4, 120),
    ]
    assert minutes_of(rows, "Keeper") == 120.0


def test_6_substitution_during_extra_time():
    """
    Titular substituído aos 110' (período 4) num jogo que vai a 120':
        titular  = 110
        suplente = 120 - 110 = 10
    """
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        substitution(1, 4, 110, "Team X", "Keeper", "Backup"),
        gk_event(1, 4, 115, "Backup", "Team X", "Shot Faced"),
        filler(1, 4, 120),
    ]
    assert minutes_of(rows, "Keeper") == 110.0
    assert minutes_of(rows, "Backup") == 10.0


def test_6b_shootout_period_does_not_add_minutes():
    """
    O período 5 é grandes penalidades. Não é tempo de jogo e não pode
    aumentar os minutos de ninguém.
    """
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        filler(1, 4, 120),
        gk_event(1, 5, 125, "Keeper", "Team X", "Penalty Saved"),
    ]
    assert minutes_of(rows, "Keeper") == 120.0


def test_7_second_keeper_on_the_bench_never_enters():
    """
    Dois guarda-redes na equipa, um deles no banco sem qualquer registo.
    Só o titular recebe minutos.
    """
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper"), ("Defender", "Center Back")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        filler(1, 2, 90),
    ]
    frame = minutes_for(rows)
    assert set(frame["player"]) == {"Keeper"}
    assert frame["minutes"].iloc[0] == 90.0


def test_8_match_without_starting_xi_is_reported_and_excluded():
    """
    Comportamento explícito: sem `Starting XI` não é possível saber quem
    começou, por isso ninguém recebe minutos nesse jogo — e o jogo é
    identificável através de `matches_without_lineup()`.

    NÃO há recurso silencioso à lógica antiga.
    """
    rows = [
        gk_event(7, 1, 10, "Keeper", "Team X", "Shot Saved"),
        filler(7, 2, 90),
    ]
    events = events_from(rows)

    assert matches_without_lineup(events) == [7]

    frame = goalkeeper_minutes_by_match(events, build_gk_events(events))
    assert frame.empty

    minutes = compute_minutes_played(events, build_gk_events(events))
    assert "Keeper" not in minutes.index


def test_sent_off_keeper_stops_accumulating_minutes():
    """
    Um guarda-redes expulso aos 83' sai do campo nesse minuto, mesmo sem
    haver substituição registada para ele.
    """
    red_card = filler(1, 2, 83)
    red_card.update(
        {
            "type": "Foul Committed",
            "player": "Keeper",
            "position": "Goalkeeper",
            "foul_committed_card": "Red Card",
        }
    )
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        red_card,
        filler(1, 2, 90),
    ]
    assert minutes_of(rows, "Keeper") == 83.0


def test_starting_lineups_ignores_tactical_shift():
    """
    `Tactical Shift` também transporta um `lineup`, mas descreve uma
    alteração a meio do jogo. Só `Starting XI` diz quem começou.
    """
    shift = starting_xi(1, "Team X", [("Impostor", "Goalkeeper")])
    shift["type"] = "Tactical Shift"
    shift["minute"] = 60

    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        shift,
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        filler(1, 2, 90),
    ]
    lineup = starting_lineups(events_from(rows))
    assert set(lineup["player"]) == {"Keeper"}
    assert minutes_of(rows, "Impostor") is None


def test_match_duration_uses_the_last_period_not_the_last_minute():
    """
    Um jogo cujo período 2 se prolonga até ao minuto 103 por compensação
    continua a valer 90 minutos regulamentares.
    """
    rows = [
        starting_xi(1, "Team X", [("Keeper", "Goalkeeper")]),
        gk_event(1, 1, 10, "Keeper", "Team X", "Shot Saved"),
        filler(1, 2, 103),
    ]
    events = events_from(rows)
    assert match_regulation_duration(events).loc[1] == 90.0
    assert minutes_of(rows, "Keeper") == 90.0


def test_period_ends_match_the_regulation_boundaries():
    assert PERIOD_ENDS == {1: 45, 2: 90, 3: 105, 4: 120}


# ---------------------------------------------------------------------------
# Validação contra um jogo real do dataset
# ---------------------------------------------------------------------------

DATASET = os.path.join("data", "events_full_wc2022.pkl")


def dataset_available(path=DATASET) -> bool:
    """
    True apenas se o ficheiro existir E for mesmo um pickle.

    Não basta `os.path.exists`: o dataset está em Git LFS, e tanto o
    `actions/checkout` do GitHub Actions como um `git clone` sem LFS deixam
    no lugar um ficheiro-ponteiro de texto com cerca de 130 bytes. Esse
    ponteiro existe, mas desserializá-lo rebenta.

    Um pickle de protocolo 2 ou superior começa sempre por 0x80; um ponteiro
    LFS começa por "version https://git-lfs...".
    """
    if not os.path.exists(path):
        return False

    with open(path, "rb") as handle:
        return handle.read(1) == b"\x80"

# Irão x Inglaterra, Mundial 2022. Beiranvand lesionou-se e foi substituído
# por Hosseini ao minuto 19 do período 1. O primeiro período prolongou-se
# até ao minuto 59 por causa da paragem, o que torna este jogo o melhor
# teste possível à conversão para o relógio regulamentar.
IRAN_ENGLAND = 3857271


@pytest.mark.skipif(
    not dataset_available(),
    reason="events_full_wc2022.pkl não disponível (ausente ou ponteiro Git LFS)",
)
def test_real_match_goalkeeper_substitution():
    events = pd.read_pickle(DATASET)
    match = events[events["match_id"] == IRAN_ENGLAND]

    frame = goalkeeper_minutes_by_match(match, build_gk_events(match))
    minutes = frame.set_index("player")["minutes"]

    # Beiranvand sai aos 19' do período 1 -> 19 minutos.
    assert minutes["Alireza Safar Beiranvand"] == 19.0

    # Hosseini entra aos 19' e o jogo é de 90 minutos regulamentares -> 71.
    assert minutes["Seyed Hossein Hosseini"] == 71.0

    # Os dois somam exatamente um jogo completo, apesar de o período 1 ter
    # terminado ao minuto 59 e o período 2 ao minuto 103 no relógio de evento.
    assert (
        minutes["Alireza Safar Beiranvand"] + minutes["Seyed Hossein Hosseini"]
        == 90.0
    )

    # O guarda-redes adversário jogou o jogo inteiro.
    assert minutes["Jordan Pickford"] == 90.0
