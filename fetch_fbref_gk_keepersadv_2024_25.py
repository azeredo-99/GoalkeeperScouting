"""
Descarrega a tabela "Advanced Goalkeeping" (keepersadv) do FBref para as
big-5 ligas europeias, época 2024/25, e guarda os resultados em CSV --
extensão de fetch_fbref_gk_2024_25.py (que já obteve a tabela "keeper"
básica). NÃO toca em `gk_performances` nem em nenhum ficheiro do
dataset existente -- este script é só de RECOLHA.

Porquê um script separado em vez de acrescentar "keeper_adv" à lista
STAT_TYPES de fetch_fbref_gk_2024_25.py: `soccerdata==1.9.1` (a versão
instalada) rejeita "keeper_adv" com TypeError antes de tentar qualquer
pedido -- read_player_season_stats() só aceita stat_type em
["standard", "keeper", "shooting", "playing_time", "misc"]. Este script
replica a MESMA lógica interna do método (confirmada lendo o código
fonte da biblioteca) para a tabela "Advanced Goalkeeping" que essa
versão não expõe publicamente -- não reimplementa scraping do zero,
reutiliza o cache/HTTP client/parser já existentes em `soccerdata`.

IMPORTANTE (proveniência dos dados): FBref/Sports Reference não permite
"spidering" nos seus Termos de Uso. Corre este script apenas no teu
próprio ambiente, por tua conta -- não faz parte da pipeline de
ingestão automática do projeto.

Uso:
    python fetch_fbref_gk_keepersadv_2024_25.py

Resultado (em data/raw/fbref/2024-25/):
    <liga>_keepersadv.csv
"""

import sys
from pathlib import Path

import pandas as pd
import soccerdata as sd
from lxml import etree, html
from soccerdata.fbref import (
    BIG_FIVE_DICT,
    FBREF_API,
    TEAMNAME_REPLACEMENTS,
    _concat,
    _fix_nation_col,
    _parse_table,
)
from soccerdata._common import standardize_colnames

SEASON = "2425"  # mesmo formato já usado em fetch_fbref_gk_2024_25.py

LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]

OUTPUT_DIR = Path("data/raw/fbref/2024-25")

STAT_TYPE = "keeper_adv"  # nome interno FBref (id da tabela: stats_keeper_adv)
PAGE = "keepersadv"  # segmento real do URL do FBref para esta tabela


def slug(league: str) -> str:
    return league.replace(" ", "_").replace("-", "_")


def read_keeper_adv_stats(fbref: sd.FBref) -> pd.DataFrame:
    """
    Réplica de FBref.read_player_season_stats(stat_type="keeper") do
    soccerdata, linha a linha igual, só com stat_type/page ajustados
    para "Advanced Goalkeeping" -- ver docstring do módulo.
    """
    filemask = "players_{}_{}_{}.html"

    seasons = fbref.read_seasons()

    players = []
    for (lkey, skey), season in seasons.iterrows():
        big_five = lkey == "Big 5 European Leagues Combined"
        filepath = fbref.data_dir / filemask.format(lkey, skey, STAT_TYPE)
        url = (
            FBREF_API
            + "/".join(season.url.split("/")[:-1])
            + f"/{PAGE}"
            + ("/players/" if big_five else "/")
            + season.url.split("/")[-1]
        )
        reader = fbref.get(url, filepath)
        tree = html.parse(reader)
        for elem in tree.xpath("//td[@data-stat='comp_level']//span"):
            elem.getparent().remove(elem)

        if big_five:
            (html_table,) = tree.xpath(f"//table[@id='stats_{STAT_TYPE}']")
            df_table = _parse_table(html_table)
            df_table[("Unnamed: league", "league")] = (
                df_table.xs("Comp", axis=1, level=1).squeeze().map(BIG_FIVE_DICT)
            )
            df_table[("Unnamed: season", "season")] = skey
            df_table.drop("Comp", axis=1, level=1, inplace=True)
        else:
            (el,) = tree.xpath(f"//comment()[contains(.,'div_stats_{STAT_TYPE}')]")
            parser = etree.HTMLParser(recover=True)
            (html_table,) = etree.fromstring(el.text, parser).xpath(
                f"//table[contains(@id, 'stats_{STAT_TYPE}')]"
            )
            df_table = _parse_table(html_table)
            df_table[("Unnamed: league", "league")] = lkey
            df_table[("Unnamed: season", "season")] = skey

        df_table = _fix_nation_col(df_table)
        players.append(df_table)

    df = _concat(players, key=["league", "season"])
    df = df[df.Player != "Player"]
    return (
        df.drop("Matches", axis=1, level=0)
        .drop("Rk", axis=1, level=0)
        .rename(columns={"Squad": "team"})
        .replace({"team": TEAMNAME_REPLACEMENTS})
        .pipe(standardize_colnames, cols=["Player", "Nation", "Pos", "Age", "Born"])
        .set_index(["league", "season", "team", "player"])
        .sort_index()
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    failed: list[str] = []

    for league in LEAGUES:
        print("=" * 70)
        print(f"{league} — {SEASON} (keepersadv)")
        print("=" * 70)

        try:
            fbref = sd.FBref(leagues=league, seasons=SEASON)
            df = read_keeper_adv_stats(fbref)
        except Exception as exc:
            print(f"  [FALHOU] {league}: {exc}")
            failed.append(league)
            continue

        out_path = OUTPUT_DIR / f"{slug(league)}_keepersadv.csv"
        df.to_csv(out_path)

        print(f"  OK — {league}")
        print(f"    ficheiro: {out_path}")
        print(f"    linhas: {len(df)}")
        print(f"    colunas: {list(df.columns)}")
        saved.append(str(out_path))

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"Ficheiros guardados ({len(saved)}):")
    for path in saved:
        print(f"  - {path}")

    if failed:
        print(f"\nFalharam ({len(failed)}):")
        for item in failed:
            print(f"  - {item}")
        sys.exit(1)


if __name__ == "__main__":
    main()
