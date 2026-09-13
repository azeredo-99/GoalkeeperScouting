"""
Descarrega estatísticas de guarda-redes do FBref (via `soccerdata`) para as
big-5 ligas europeias, época 2024/25, e guarda os resultados em CSV para
inspeção manual -- NÃO toca em `gk_performances` nem em nenhum ficheiro do
dataset existente.

Este script é deliberadamente só de RECOLHA. O mapeamento FBref -> schema
do projeto, a coluna `source`, e a integração no benchmark ficam para depois
de confirmarmos as colunas reais devolvidas (ver README/aviso no fim deste
ficheiro).

IMPORTANTE (proveniência dos dados): FBref/Sports Reference não permite
"spidering" nos seus Termos de Uso. Corre este script apenas no teu próprio
ambiente, por tua conta -- não faz parte da pipeline de ingestão automática
do projeto.

Uso:
    python fetch_fbref_gk_2024_25.py

Resultado (em data/raw/fbref/2024-25/):
    <liga>_keeper.csv
    <liga>_keeper_adv.csv

Requer `soccerdata` instalado (não está em requirements.txt de propósito --
ver aviso acima).
"""

import sys
from pathlib import Path

import soccerdata as sd

SEASON = "2425"  # formato soccerdata para a época 2024/2025

LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]

STAT_TYPES = ["keeper", "keeper_adv"]

OUTPUT_DIR = Path("data/raw/fbref/2024-25")


def slug(league: str) -> str:
    return league.replace(" ", "_").replace("-", "_")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    failed: list[str] = []

    for league in LEAGUES:
        print("=" * 70)
        print(f"{league} — {SEASON}")
        print("=" * 70)

        try:
            fbref = sd.FBref(leagues=league, seasons=SEASON)
        except Exception as exc:
            print(f"  [FALHOU] não foi possível inicializar o reader para {league}: {exc}")
            failed.append(f"{league} (init)")
            continue

        for stat_type in STAT_TYPES:
            label = f"{league} / {stat_type}"
            try:
                df = fbref.read_player_season_stats(stat_type=stat_type)
            except Exception as exc:
                print(f"  [FALHOU] {label}: {exc}")
                failed.append(label)
                continue

            out_path = OUTPUT_DIR / f"{slug(league)}_{stat_type}.csv"
            df.to_csv(out_path)

            print(f"  OK — {label}")
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
