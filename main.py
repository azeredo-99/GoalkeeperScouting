"""
Projeto: Algoritmo de Perfilagem de Guarda-Redes
--------------------------------------------------
Pipeline completo de scouting de guarda-redes usando dados reais
e gratuitos da StatsBomb (Mundial 2022).

Corre com:
    python main.py

Resultado (em output/):
    - scouting_table.csv     -> tabela com todas as métricas por guarda-redes
    - radar_comparativo.png  -> radar comparando os guarda-redes escolhidos
    - sweeper_map_<jogador>.png -> mapa de saídas da baliza do guarda-redes escolhido

Para adaptar a outra competição, basta mudar COMPETITION_ID / SEASON_ID
(ver a lista completa correndo `statsbombpy.sb.competitions()`).
"""

import os

import _bootstrap  # noqa: F401  (coloca src/ no sys.path)

from gk_scouting.data_loader import load_competition_events, build_gk_events, build_gk_passes
from gk_scouting.metrics import build_scouting_table
from gk_scouting.visuals import plot_radar, plot_sweeper_map
from gk_scouting.similarity_engine import find_similar_goalkeepers, explain_similarity
from gk_scouting.readable_report import build_readable_table, build_scouting_report, build_similarity_report, build_full_table_report

# ---- CONFIGURAÇÃO ---------------------------------------------------------
COMPETITION_ID = 43   # FIFA World Cup
SEASON_ID = 106        # 2022

# MATCH_IDS = None -> descarrega TODOS os jogos da competição (recomendado,
# demora ~3-5 min na primeira vez, depois fica em cache). Para testar rápido,
# passa uma lista de match_id (ver sb.matches(competition_id, season_id)).
MATCH_IDS = None

# Amostra mínima de minutos para um guarda-redes entrar nas comparações
# (evita tirar conclusões de guarda-redes que só jogaram 10 minutos)
MIN_MINUTES = 180

# Guarda-redes a comparar no radar
PLAYERS_TO_COMPARE = [
    "Damián Emiliano Martínez",
    "Yassine Bounou",
    "Dominik Livaković",
]

# Guarda-redes cujo mapa de saídas da baliza queremos ver em detalhe
PLAYER_FOR_SWEEPER_MAP = "Damián Emiliano Martínez"

# Guarda-redes para o qual queremos encontrar "parecidos" (algoritmo de similaridade)
FIND_SIMILAR_TO = "Manuel Neuer"

OUTPUT_DIR = "output"
CACHE_PATH = os.path.join("data", "events_full_wc2022.pkl")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # 1. Carregar eventos (usa cache local se já tiveres corrido antes)
    if os.path.exists(CACHE_PATH):
        import pandas as pd
        print("A usar dados em cache...")
        events = pd.read_pickle(CACHE_PATH)
    else:
        print("A descarregar dados da StatsBomb...")
        events = load_competition_events(COMPETITION_ID, SEASON_ID, match_ids=MATCH_IDS)
        events.to_pickle(CACHE_PATH)

    # 2. Isolar eventos e passes de guarda-redes
    gk_events = build_gk_events(events)
    gk_passes = build_gk_passes(events)

    # 3. Calcular a tabela de métricas de scouting
    table = build_scouting_table(events, gk_events, gk_passes)
    table.round(2).to_csv(os.path.join(OUTPUT_DIR, "scouting_table.csv"), encoding="utf-8-sig")

    table_robust = table[table["minutes"] >= MIN_MINUTES]
    print(f"\n{len(table_robust)} guarda-redes com >= {MIN_MINUTES} minutos jogados\n")
    print(table_robust.round(1).to_string())

    # 4. Algoritmo de similaridade: "encontrar o novo X"
    print(f"\nGuarda-redes parecidos com {FIND_SIMILAR_TO}:\n")
    similar = find_similar_goalkeepers(table_robust, FIND_SIMILAR_TO, top_n=5)
    print(similar[["similarity_pct", "minutes"]].round(1).to_string())
    for candidate in similar.index:
        print(" -", explain_similarity(table_robust, FIND_SIMILAR_TO, candidate))
    similar.round(2).to_csv(os.path.join(OUTPUT_DIR, f"similar_to_{FIND_SIMILAR_TO.split()[-1].lower()}.csv"), encoding="utf-8-sig")

    # 5. Relatório combinado em texto: tabela completa + similaridade, tudo num só ficheiro.
    # Gravado ANTES dos gráficos de propósito: se o matplotlib falhar por qualquer razão
    # (fontes, permissões, etc.), este ficheiro já está garantido no disco.
    combined_report = (
        build_full_table_report(table_robust)
        + "\n\n\n"
        + build_similarity_report(table_robust, FIND_SIMILAR_TO, similar, explain_similarity)
    )
    combined_report_path = os.path.join(OUTPUT_DIR, "relatorio_completo.txt")
    with open(combined_report_path, "w", encoding="utf-8") as f:
        f.write(combined_report)
    print(f"\n[gravado] {combined_report_path}")

    # 6. Gerar visualizações
    plot_radar(table_robust, PLAYERS_TO_COMPARE, os.path.join(OUTPUT_DIR, "radar_comparativo.png"))

    safe_name = PLAYER_FOR_SWEEPER_MAP.lower().replace(" ", "_")
    plot_sweeper_map(gk_events, PLAYER_FOR_SWEEPER_MAP,
                      os.path.join(OUTPUT_DIR, f"sweeper_map_{safe_name}.png"))

    print(f"\nFicheiros gerados em ./{OUTPUT_DIR}/")
    print("Para a versão interativa: streamlit run streamlit_app.py")

    # 7. Versão legível para humanos (nomes em português, sem ruído técnico)
    readable = build_readable_table(table_robust)
    readable.to_csv(os.path.join(OUTPUT_DIR, "tabela_legivel.csv"), encoding="utf-8-sig")

    report_text = build_scouting_report(table_robust)
    with open(os.path.join(OUTPUT_DIR, "relatorio_scouting.txt"), "w", encoding="utf-8") as f:
        f.write(report_text)
    print(report_text)


if __name__ == "__main__":
    main()