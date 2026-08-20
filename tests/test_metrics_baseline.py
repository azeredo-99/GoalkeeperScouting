"""
Baseline de regressão das métricas, antes do P0-2.

O P0-2 vai substituir a forma como os minutos são calculados. Esta suite
existe para tornar visível o que essa alteração muda e o que não pode mudar.

Os testes estão divididos em três grupos, e a divisão é o ponto principal:

    ESPERA-SE QUE MUDEM     `minutes` e tudo o que dele deriva (p90, ordem).
                            Os valores aqui registados são os atuais, não
                            os corretos. Quando o P0-2 os alterar, estes
                            testes falham de propósito e devem ser
                            atualizados com justificação.

    NÃO PODEM MUDAR         Métricas independentes de minutos. Se algum
                            destes falhar depois do P0-2, é regressão.

    CONTRATO                Estrutura da tabela: colunas e índice.

Todos os valores esperados são calculados à mão a partir do dataset
sintético em `conftest.py`; a aritmética está nos comentários.
"""

import numpy as np
import pandas as pd
import pytest

from gk_scouting.metrics import compute_minutes_played
from gk_scouting.data_loader import build_gk_events

from conftest import EVENT_COLUMNS, filler, gk_event, starting_xi


# ===========================================================================
# GRUPO 1 — MINUTOS  (atualizado pelo P0-2)
# ===========================================================================
#
# Estes valores foram atualizados quando o P0-2 substituiu a inferencia por
# eventos `Goal Keeper` pelo calculo baseado em `Starting XI` + substituicoes.
# O que cada teste afirmava ANTES esta registado na respetiva docstring, para
# que a alteracao continue legivel.

def test_minutes_come_from_lineups_and_substitutions(synthetic_table):
    """
        Keeper A : jogo 1 completo (90) + jogo 2 completo (120) = 210
        Keeper B : jogo 1 completo                              =  90
        Keeper C : titular do jogo 3, substituido aos 60'       =  60
        Keeper D : entra no jogo 3 aos 60', jogo acaba aos 90'  =  30

    ANTES do P0-2: A=210, B=90, C=90, D=90 -- C e D recebiam ambos o jogo
    inteiro por terem eventos nele.
    """
    minutes = synthetic_table["minutes"]
    assert minutes["Keeper A"] == 210.0
    assert minutes["Keeper B"] == 90.0
    assert minutes["Keeper C"] == 60.0
    assert minutes["Keeper D"] == 30.0


def test_match_duration_comes_from_the_last_period_not_the_last_minute(synthetic_table):
    """
    A duracao regulamentar deriva do ultimo periodo do jogo (2 -> 90,
    4 -> 120), nao do minuto maximo observado. O minuto maximo inclui tempo
    de compensacao e, no StatsBomb, os periodos sobrepoem-se no relogio.

    Jogo 1 termina no periodo 2 e o jogo 2 no periodo 4.
    """
    assert synthetic_table.loc["Keeper A", "minutes"] == 90.0 + 120.0


def test_extra_time_gives_one_hundred_and_twenty_to_who_played_it(synthetic_table):
    """
    O prolongamento continua a valer 120 minutos -- mas so para quem esteve
    em campo. ANTES, qualquer guarda-redes com um evento no jogo recebia a
    duracao completa, mesmo tendo saido antes do prolongamento.
    """
    assert synthetic_table.loc["Keeper A", "minutes"] - 90.0 == 120.0


def test_substitute_keeper_only_gets_the_time_he_was_on_the_pitch(synthetic_table):
    """
    ANTES (M3, incorreto): o suplente recebia o jogo inteiro, 90 minutos.
    AGORA: entra aos 60', o jogo acaba aos 90', logo 30 minutos.

    E o titular que sai fica com os 60 que jogou, e nao com 90.
    """
    assert synthetic_table.loc["Keeper D", "minutes"] == 30.0
    assert synthetic_table.loc["Keeper C", "minutes"] == 60.0
    assert (
        synthetic_table.loc["Keeper C", "minutes"]
        + synthetic_table.loc["Keeper D", "minutes"]
        == 90.0
    )


def test_keeper_with_events_but_never_on_the_pitch_gets_no_minutes():
    """
    ANTES: bastava ter um evento `Goal Keeper` para receber minutos.
    AGORA: e preciso estar no onze inicial ou ter entrado como substituto.
    Ter eventos registados nao prova presenca em campo.
    """
    events = pd.DataFrame(
        [
            starting_xi(1, "Team X", [("Real Keeper", "Goalkeeper")]),
            gk_event(1, 1, 10, "Real Keeper", "Team X", "Shot Saved"),
            gk_event(1, 1, 20, "Ghost Keeper", "Team X", "Shot Saved"),
            filler(1, 2, 90),
        ],
        columns=EVENT_COLUMNS,
    )
    minutes = compute_minutes_played(events, build_gk_events(events))
    assert minutes["Real Keeper"] == 90.0
    assert "Ghost Keeper" not in minutes.index


def test_table_is_sorted_by_minutes_descending(synthetic_table):
    assert synthetic_table.index[0] == "Keeper A"
    assert synthetic_table["minutes"].is_monotonic_decreasing


# ---------------------------------------------------------------------------
# Métricas por 90 (derivadas dos minutos)
# ---------------------------------------------------------------------------

def test_shots_faced_p90_baseline(synthetic_table):
    """
        Keeper A : 9 / 210 * 90 = 3.857142...
        Keeper B : 3 /  90 * 90 = 3.0
        Keeper C : 2 /  60 * 90 = 3.0   (antes 2.0, com 90 minutos)
        Keeper D : 1 /  30 * 90 = 3.0   (antes 1.0, com 90 minutos)

    O caso do Keeper D e o mais claro: um guarda-redes que enfrentou um
    remate em 30 minutos passou a ter a mesma taxa por 90 de quem enfrentou
    tres em 90 -- que e o que a metrica deve dizer.
    """
    p90 = synthetic_table["shots_faced_p90"]
    assert p90["Keeper A"] == pytest.approx(9 / 210 * 90)
    assert p90["Keeper B"] == pytest.approx(3.0)
    assert p90["Keeper C"] == pytest.approx(3.0)
    assert p90["Keeper D"] == pytest.approx(3.0)


def test_sweeper_actions_p90_baseline(synthetic_table):
    """Keeper A: 2 / 210 * 90 = 0.857142... (inalterado pelo P0-2)"""
    assert synthetic_table.loc["Keeper A", "sweeper_actions_p90"] == pytest.approx(2 / 210 * 90)


def test_sweeper_p90_is_nan_when_the_keeper_never_swept(synthetic_table):
    """
    ATUAL: zero saidas nao produz 0.0 -- produz NaN, porque o guarda-redes
    nao aparece de todo em `sweeper_keeper_metrics`. E a exclusao silenciosa
    descrita em M5/S3; nao e afetada pelo P0-2 e continua por resolver.
    """
    for keeper in ("Keeper B", "Keeper C", "Keeper D"):
        assert np.isnan(synthetic_table.loc[keeper, "sweeper_actions"])
        assert np.isnan(synthetic_table.loc[keeper, "sweeper_actions_p90"])


# ===========================================================================
# GRUPO 2 — INDEPENDENTES DOS MINUTOS  (o P0-2 NÃO pode alterar isto)
# ===========================================================================

def test_save_pct_baseline(synthetic_table):
    """
        Keeper A : 4 / (4 + 1) = 80 %
        Keeper B : 1 / (1 + 1) = 50 %
        Keeper C : 2 / (2 + 0) = 100 %
        Keeper D : sem remates enquadrados -> NaN
    """
    save_pct = synthetic_table["save_pct"]
    assert save_pct["Keeper A"] == pytest.approx(80.0)
    assert save_pct["Keeper B"] == pytest.approx(50.0)
    assert save_pct["Keeper C"] == pytest.approx(100.0)
    assert np.isnan(save_pct["Keeper D"])


def test_shot_counts_baseline(synthetic_table):
    """
    `shots_faced` = enquadrados (defendidos + sofridos) + não enquadrados.

        Keeper A : (4 + 1) + 4 = 9
        Keeper B : (1 + 1) + 1 = 3
        Keeper C : (2 + 0) + 0 = 2
        Keeper D : (0 + 0) + 1 = 1
    """
    expected = {
        "Keeper A": (9, 4, 1),
        "Keeper B": (3, 1, 1),
        "Keeper C": (2, 2, 0),
        "Keeper D": (1, 0, 0),
    }
    for keeper, (faced, saved, conceded) in expected.items():
        row = synthetic_table.loc[keeper]
        assert row["shots_faced"] == faced
        assert row["shots_saved"] == saved
        assert row["goals_conceded"] == conceded


def test_distribution_baseline(synthetic_table):
    """
    Keeper A — 5 passes de 20/30/50/60/40, sendo 3 completos:
        total_passes      = 5
        pass_success_pct  = 3/5           = 60 %
        avg_pass_length   = 200/5         = 40
        long_ball_pct     = 2/5 (>40)     = 40 %   (40 não conta: é `> 40`)
    """
    a = synthetic_table.loc["Keeper A"]
    assert a["total_passes"] == 5
    assert a["pass_success_pct"] == pytest.approx(60.0)
    assert a["avg_pass_length"] == pytest.approx(40.0)
    assert a["long_ball_pct"] == pytest.approx(40.0)

    b = synthetic_table.loc["Keeper B"]
    assert b["total_passes"] == 2
    assert b["pass_success_pct"] == pytest.approx(100.0)
    assert b["avg_pass_length"] == pytest.approx(20.0)
    assert b["long_ball_pct"] == pytest.approx(0.0)

    c = synthetic_table.loc["Keeper C"]
    assert c["avg_pass_length"] == pytest.approx(45.0)
    assert c["long_ball_pct"] == pytest.approx(100.0)


def test_long_ball_threshold_is_strictly_greater_than_forty(synthetic_table):
    """Um passe de exatamente 40 metros não conta como bola longa."""
    assert synthetic_table.loc["Keeper A", "long_ball_pct"] == pytest.approx(40.0)


def test_sweeper_distances_baseline(synthetic_table):
    """
    Saídas do Keeper A em [3, 44] e [6, 48]; baliza própria em (0, 40):
        hypot(3, 4)  =  5
        hypot(6, 8)  = 10
        média = 7.5, máximo = 10
    """
    a = synthetic_table.loc["Keeper A"]
    assert a["sweeper_actions"] == 2
    assert a["avg_distance_from_goal"] == pytest.approx(7.5)
    assert a["max_distance_from_goal"] == pytest.approx(10.0)


def test_minutes_independent_metrics_are_stable_under_minute_changes(synthetic_events):
    """
    A propriedade central desta baseline: mexer nos minutos dos eventos não
    pode alterar nenhuma métrica que não derive de minutos. É este o teste
    que apanha uma regressão do P0-2.

    Repara que NÃO se afirma aqui que os minutos mudam — isso depende da
    implementação de minutos e passaria a dar falso alarme assim que o P0-2
    a substituir. O comportamento dos minutos em si é coberto pelo grupo 1.
    """
    from gk_scouting.data_loader import build_gk_passes
    from gk_scouting.metrics import build_scouting_table

    def table_for(events):
        return build_scouting_table(events, build_gk_events(events), build_gk_passes(events))

    original = table_for(synthetic_events)

    stretched_events = synthetic_events.copy()
    stretched_events["minute"] = stretched_events["minute"] * 2
    stretched = table_for(stretched_events)

    independent = [
        "shots_faced", "shots_saved", "goals_conceded", "save_pct",
        "sweeper_actions", "avg_distance_from_goal", "max_distance_from_goal",
        "total_passes", "pass_success_pct", "avg_pass_length", "long_ball_pct",
    ]
    pd.testing.assert_frame_equal(
        original[independent].sort_index(),
        stretched[independent].sort_index(),
    )


# ===========================================================================
# GRUPO 3 — CONTRATO DA TABELA
# ===========================================================================

EXPECTED_COLUMNS = [
    "minutes",
    "sweeper_actions",
    "avg_distance_from_goal",
    "max_distance_from_goal",
    "shots_faced",
    "shots_saved",
    "goals_conceded",
    "save_pct",
    "total_passes",
    "pass_success_pct",
    "avg_pass_length",
    "long_ball_pct",
    "sweeper_actions_p90",
    "shots_faced_p90",
]


def test_table_columns_are_exactly_the_expected_set(synthetic_table):
    """
    Fixa a superfície da tabela. Se o P0-2 acrescentar colunas (por exemplo
    `saves_p90` ou `goals_conceded_p90`, que hoje NÃO existem) ou remover
    alguma, este teste falha e obriga a decisão a ser explícita.
    """
    assert list(synthetic_table.columns) == EXPECTED_COLUMNS


def test_per_ninety_columns_are_limited_to_the_current_two(synthetic_table):
    """Hoje só existem dois p90. Registado para o P0-2 decidir conscientemente."""
    p90_columns = [c for c in synthetic_table.columns if c.endswith("_p90")]
    assert p90_columns == ["sweeper_actions_p90", "shots_faced_p90"]


def test_index_is_the_player_name(synthetic_table):
    """
    ATUAL: a chave é o nome. É o problema M4 (falta `player_id`); registado
    aqui para que uma mudança de chave seja uma decisão visível.
    """
    assert synthetic_table.index.name == "player"
    assert set(synthetic_table.index) == {"Keeper A", "Keeper B", "Keeper C", "Keeper D"}


def test_one_row_per_keeper(synthetic_table):
    assert len(synthetic_table) == 4
    assert synthetic_table.index.is_unique
