"""
gk_scouting.fbref_mapping
--------------------------
Transformação pura (sem I/O de rede nem de BD) das estatísticas de
guarda-redes do FBref (tabela "Goalkeeping" básica, via `soccerdata`,
CSVs em data/raw/fbref/2024-25/) para o schema de `gk_performances`.

Âmbito deliberadamente limitado ao que a tabela `keeper` do soccerdata
1.9.1 realmente contém -- `keeper_adv` não existe nesta versão (ver
auditoria prévia). Os campos de Sweeping/Distribution não têm
equivalente nesta fonte e ficam sempre `None`, nunca `0` -- ausência de
dado não é o mesmo que mau desempenho (mesmo princípio de metrics.py).

Diferenças de definição registadas, não escondidas:

* `shots_faced` (StatsBomb, metrics.py) = remates enquadrados + não
  enquadrados. Aqui vem de `SoTA` (Shots on Target Against) -- SÓ
  remates enquadrados. Mesmo nome, métrica diferente.
* `save_pct`: para um jogador com uma só linha (um só clube na época),
  usa-se o `Save%` já calculado pela própria FBref, sem o recalcular --
  a fórmula deles pode tratar casos-limite (ex. grandes penalidades) de
  forma ligeiramente diferente da nossa e não vale a pena fingir
  precisão que não temos. Só se recalcula quando agregamos duas linhas
  do mesmo jogador (ver `aggregate_multi_club_rows`), porque nesse caso
  não existe um único `Save%` da FBref que sirva -- duas percentagens
  de amostras diferentes não são combináveis por média direta.

É por isto que `gk_performances.source` existe: mesmo os campos com
"correspondência direta" ao StatsBomb não são a mesma métrica.
"""

from pathlib import Path

import pandas as pd

SOURCE = "fbref"

# IDs sintéticos -- fora da gama de competition_id/season_id que o
# StatsBomb Open Data usa (o maior competition_id real é 1267). Um
# season_id só, partilhado pelas 5 ligas, tal como o StatsBomb já
# reutiliza um season_id entre competições do mesmo ano (ex.: season_id
# 27 = 2015/16 para La Liga/Premier League/Serie A/Ligue 1).
FBREF_SEASON_ID = 900001
FBREF_SEASON_NAME = "2024/2025"

# Chave = valor da coluna "league" nos CSVs (vem do soccerdata).
FBREF_COMPETITIONS = {
    "ENG-Premier League": (900001, "Premier League"),
    "ESP-La Liga": (900002, "La Liga"),
    "GER-Bundesliga": (900003, "1. Bundesliga"),
    "ITA-Serie A": (900004, "Serie A"),
    "FRA-Ligue 1": (900005, "Ligue 1"),
}

# Nome do ficheiro (ver fetch_fbref_gk_2024_25.py) -> valor da coluna
# "league" dentro desse CSV. Evita adivinhar o nome do ficheiro a partir
# do dicionário acima -- os dois vocabulários (nome de ficheiro vs.
# código de liga do soccerdata) são propositadamente independentes.
RAW_CSV_FILES = [
    "ENG_Premier_League_keeper.csv",
    "ESP_La_Liga_keeper.csv",
    "GER_Bundesliga_keeper.csv",
    "ITA_Serie_A_keeper.csv",
    "FRA_Ligue_1_keeper.csv",
]

# Colunas somadas ao agregar um jogador com mais do que um clube na
# mesma época. `Save%` e `CS%` ficam de fora de propósito -- são
# derivadas, recalculam-se depois da soma (ver aggregate_multi_club_rows).
_SUMMABLE_COLUMNS = [
    "MP", "Starts", "90s", "GA", "SoTA", "Saves", "W", "D", "L",
    "PKatt", "PKA", "PKsv", "PKm", "Min",
]

# Colunas finais que este módulo garante preencher em todas as linhas
# que devolve -- exatamente as que já existem em GKPerformance, mais
# `source`. As de Sweeping/Distribution aparecem aqui só para deixar
# explícito que são sempre None nesta fonte (ver _NEVER_AVAILABLE).
GK_PERFORMANCE_COLUMNS = [
    "minutes", "shots_faced", "shots_saved", "goals_conceded", "save_pct",
    "shots_faced_p90", "sweeper_actions", "avg_distance_from_goal",
    "max_distance_from_goal", "sweeper_actions_p90", "total_passes",
    "pass_success_pct", "avg_pass_length", "long_ball_pct", "source",
]

# Campos que esta fonte nunca preenche. Lista à parte para que, ao ler
# o código, fique claro que é uma decisão (tabela `keeper_adv` da FBref
# não disponível nesta versão do soccerdata) e não um esquecimento.
_NEVER_AVAILABLE_FIELDS = [
    "sweeper_actions", "sweeper_actions_p90", "avg_distance_from_goal",
    "max_distance_from_goal", "total_passes", "pass_success_pct",
    "avg_pass_length", "long_ball_pct",
]


def load_raw_keeper_csv(path) -> pd.DataFrame:
    """
    Lê um CSV produzido por `fetch_fbref_gk_2024_25.py`, respeitando o
    cabeçalho real de duas linhas (grupo + métrica, ex. "Playing Time" /
    "Min") e o índice (league, season, team, player) que o soccerdata
    produz.

    `header=0` simples corrompe isto em colunas "Unnamed: N" -- foi
    assim que a auditoria inicial leu os CSVs errado antes de se
    confirmar a estrutura real linha a linha.

    A coluna "Save%" existe duas vezes no ficheiro (uma em
    "Performance", a percentagem de defesas; outra em "Penalty Kicks",
    a percentagem de penalties defendidos) -- desambiguadas aqui para
    "Save%" e "PK_Save%" respetivamente.
    """
    df = pd.read_csv(path, header=[0, 1], index_col=[0, 1, 2, 3])

    columns = []
    for group, metric in df.columns:
        if not metric or str(metric).startswith("Unnamed"):
            columns.append(group)
        elif metric == "Save%" and group == "Penalty Kicks":
            columns.append("PK_Save%")
        else:
            columns.append(metric)
    df.columns = columns

    df.index.names = ["league", "season", "team", "player"]
    return df.reset_index()


def load_all_raw_keeper_csvs(directory) -> pd.DataFrame:
    """Lê e concatena os 5 CSVs das big-5 ligas a partir de `directory`."""
    directory = Path(directory)
    frames = [load_raw_keeper_csv(directory / name) for name in RAW_CSV_FILES]
    return pd.concat(frames, ignore_index=True)


def aggregate_multi_club_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Junta as linhas de um jogador que mudou de clube a meio da época
    2024/25 numa só. A tabela `keeper` do FBref não devolve uma linha
    agregada para estes casos (confirmado na auditoria: Brice Samba,
    Lens -> Rennes, Ligue 1; Elia Caprile e Simone Scuffet,
    Cagliari <-> Napoli, Serie A -- casos reais nos dados, não
    hipotéticos).

    Estratégia (aprovada explicitamente, não inventada aqui):
    - soma os totais brutos em `_SUMMABLE_COLUMNS`;
    - NÃO soma nem tira média de `Save%`/`PK_Save%` -- ficam marcadas
      como recalculadas depois (ver `_recompute_save_pct`), porque a
      média de duas percentagens de amostras diferentes não é a
      percentagem combinada correta;
    - `team` fica "Multiple clubs" só para leitura humana -- nunca é
      usado como chave em lado nenhum desta pipeline.

    Um jogador com uma só linha na época passa por esta função
    inalterado (grupo de tamanho 1).
    """
    df = df.copy()
    df["_n_teams"] = df.groupby(["league", "season", "player"])["team"].transform("nunique")

    single = df[df["_n_teams"] <= 1].drop(columns="_n_teams")

    multi = df[df["_n_teams"] > 1].drop(columns="_n_teams")
    if multi.empty:
        return single.reset_index(drop=True)

    grouped = multi.groupby(["league", "season", "player"], as_index=False)
    summed = grouped[_SUMMABLE_COLUMNS].sum()
    summed["team"] = "Multiple clubs"

    # Colunas de identidade que não fazem sentido somar (nation/pos/age/
    # born) -- fica o primeiro valor observado, só para não perder a
    # coluna; nenhuma delas é usada a jusante no mapping para
    # GKPerformance.
    passthrough_cols = [c for c in multi.columns if c not in _SUMMABLE_COLUMNS and c not in ("league", "season", "player", "team")]
    first_values = grouped[passthrough_cols].first()
    aggregated = summed.merge(first_values, on=["league", "season", "player"])

    aggregated = _recompute_save_pct(aggregated)

    return pd.concat([single, aggregated], ignore_index=True, sort=False)


def _recompute_save_pct(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalcula `Save%` a partir de `Saves`/`SoTA` já somados -- só usada
    para linhas agregadas (ver aggregate_multi_club_rows). Confirmado
    nos dados reais que Saves == SoTA - GA (ex. Raya: SoTA=120,
    Saves=86, GA=34), por isso Saves/SoTA*100 é a mesma fórmula que a
    FBref usa por linha, só aplicada aos totais somados.

    `None` quando SoTA somado é 0 -- nunca 0%, pelo mesmo motivo que
    metrics.py nunca transforma "sem remates enquadrados" em "0% de
    defesas" (ver shot_stopping_metrics).
    """
    df = df.copy()
    df["Save%"] = df.apply(
        lambda row: (row["Saves"] / row["SoTA"] * 100) if row["SoTA"] > 0 else None,
        axis=1,
    )
    return df


def _shots_faced_p90(shots_faced, minutes):
    if minutes is None or minutes <= 0:
        return None
    return shots_faced / minutes * 90


def fbref_row_to_gk_performance(row: pd.Series) -> dict:
    """
    Converte uma linha já agregada (ver `aggregate_multi_club_rows`)
    para exatamente as colunas de `GKPerformance` que esta fonte pode
    preencher, mais `player`/`competition_id`/`season_id` (chave) e
    `source`.

    Os campos de Sweeping/Distribution ficam sempre `None`
    (`_NEVER_AVAILABLE_FIELDS`) -- não existem na tabela `keeper` básica
    do FBref (ver docstring do módulo).
    """
    league = row["league"]
    if league not in FBREF_COMPETITIONS:
        raise ValueError(f"Liga FBref desconhecida: {league!r} -- confirma FBREF_COMPETITIONS.")
    competition_id, _ = FBREF_COMPETITIONS[league]

    minutes = float(row["Min"])
    shots_faced = float(row["SoTA"])
    save_pct = row["Save%"]
    save_pct = None if pd.isna(save_pct) else float(save_pct)

    record = {
        "player": row["player"],
        "competition_id": competition_id,
        "season_id": FBREF_SEASON_ID,
        "source": SOURCE,
        "minutes": minutes,
        "shots_faced": shots_faced,
        "shots_saved": float(row["Saves"]),
        "goals_conceded": float(row["GA"]),
        "save_pct": save_pct,
        "shots_faced_p90": _shots_faced_p90(shots_faced, minutes),
    }
    for field in _NEVER_AVAILABLE_FIELDS:
        record[field] = None

    return record


def build_fbref_table(directory) -> pd.DataFrame:
    """
    Pipeline completo (mas sem I/O de BD): lê os 5 CSVs de `directory`,
    agrega jogadores multi-clube, mapeia para o schema de
    `gk_performances`, e devolve uma tabela indexada por
    (player, competition_id, season_id) -- a mesma forma que
    `build_scouting_table(..., context_columns=...)` produz para o
    StatsBomb, para poder reutilizar `db.ingest.table_to_records` sem
    alterações.
    """
    raw = load_all_raw_keeper_csvs(directory)
    aggregated = aggregate_multi_club_rows(raw)

    records = [fbref_row_to_gk_performance(row) for _, row in aggregated.iterrows()]
    table = pd.DataFrame.from_records(records)
    table = table.rename(columns={"player": "player"}).set_index(["player", "competition_id", "season_id"])

    return table[GK_PERFORMANCE_COLUMNS]
