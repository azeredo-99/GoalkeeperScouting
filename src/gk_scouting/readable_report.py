"""
gk_scouting.readable_report
-----------------------------
A tabela técnica (scouting_table.csv) é ótima para código, mas ilegível
para uma leitura rápida. Este módulo gera duas coisas mais amigáveis:

1. Um CSV com colunas em português e valores arredondados, pronto a abrir
   no Excel sem teres de saber o que cada coluna técnica significa.
2. Um "relatório de scouting" em texto — como um scout escreveria,
   com o top 5 de cada categoria e uma frase a explicar cada um.
"""

import pandas as pd

# Nome técnico -> nome legível em português
COLUMN_LABELS = {
    "minutes": "Minutos jogados",
    "sweeper_actions_p90": "Saídas da baliza por jogo",
    "avg_distance_from_goal": "Distância média a que atua (m)",
    "save_pct": "% de remates defendidos",
    "shots_faced_p90": "Remates sofridos por jogo",
    "pass_success_pct": "% de passes certos",
    "avg_pass_length": "Comprimento médio do passe (m)",
    "long_ball_pct": "% de bola longa",
    "goals_conceded": "Golos sofridos (na amostra)",
    "shots_faced": "Remates sofridos (na amostra)",
    "shots_saved": "Remates defendidos (na amostra)",
}

# As colunas e ordem que interessam para uma leitura humana
# (deixamos de fora as contagens absolutas menos intuitivas, como sweeper_actions em bruto)
READABLE_COLUMNS = [
    "minutes",
    "save_pct",
    "shots_faced_p90",
    "sweeper_actions_p90",
    "avg_distance_from_goal",
    "pass_success_pct",
    "avg_pass_length",
    "long_ball_pct",
]


def build_readable_table(table: pd.DataFrame) -> pd.DataFrame:
    """
    Devolve uma versão da tabela só com as colunas relevantes,
    renomeadas para português, arredondadas, e ordenada pela
    eficácia de defesas (a métrica mais intuitiva primeiro).
    """
    readable = table[READABLE_COLUMNS].copy()
    readable = readable.round(1)
    readable = readable.sort_values("save_pct", ascending=False)
    readable.columns = [COLUMN_LABELS[c] for c in readable.columns]
    readable.index.name = "Guarda-redes"
    return readable


def build_similarity_report(table: pd.DataFrame, target_player: str, similar: pd.DataFrame, explain_fn) -> str:
    """
    Gera um relatório em texto (estilo scouting) com os guarda-redes mais
    parecidos a `target_player`, incluindo a explicação de onde se parecem
    e onde diferem. `similar` é o resultado de find_similar_goalkeepers().
    `explain_fn` é a função explain_similarity() do similarity_engine
    (passada como argumento para não criar dependência circular entre módulos).
    """
    lines = []
    lines.append("=" * 60)
    lines.append(f"GUARDA-REDES PARECIDOS COM {target_player.upper()}")
    lines.append("=" * 60)
    lines.append("")

    # tabela numérica (a mesma que aparece no terminal), para quem quer os números em bruto
    numeric_table = similar[["similarity_pct", "minutes"]].round(1)
    numeric_table.columns = ["Similaridade (%)", "Minutos jogados"]
    lines.append(numeric_table.to_string())
    lines.append("")
    lines.append("-" * 60)
    lines.append("Leitura de scouting:")
    lines.append("")

    for rank, (player, row) in enumerate(similar.iterrows(), start=1):
        lines.append(f"{rank}. {player}")
        lines.append(f"   Similaridade: {row['similarity_pct']:.1f}%")
        lines.append(f"   Minutos jogados na amostra: {row['minutes']:.0f}")
        lines.append(f"   {explain_fn(table, target_player, player)}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("Nota: a similaridade compara o ESTILO de jogo (proatividade a sair da")
    lines.append("baliza, distribuição, eficácia de defesas), não a qualidade absoluta.")
    lines.append("Um candidato pode ser muito parecido e, ainda assim, pior ou melhor jogador.")
    return "\n".join(lines)


def build_full_table_report(table: pd.DataFrame) -> str:
    """
    Grava a tabela técnica completa (todas as colunas, todos os guarda-redes)
    exatamente como aparece impressa no terminal ao correr main.py.
    Complementa a tabela_legivel.csv (que só tem as colunas mais intuitivas)
    e o scouting_table.csv (que é a versão "crua" para código).
    """
    lines = []
    lines.append("=" * 60)
    lines.append("TABELA COMPLETA DE MÉTRICAS — TODOS OS GUARDA-REDES")
    lines.append("=" * 60)
    lines.append("")
    lines.append(table.round(1).to_string())
    return "\n".join(lines)


def build_scouting_report(table: pd.DataFrame, top_n: int = 5) -> str:
    """
    Gera um relatório em texto (como um scout escreveria), com o top N
    de cada categoria, em vez de uma tabela só com números.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("RELATÓRIO DE SCOUTING — GUARDA-REDES")
    lines.append("=" * 60)

    categories = [
        ("save_pct", "Melhor eficácia de defesas", "% remates defendidos", True),
        ("sweeper_actions_p90", "Mais proativos a sair da baliza (estilo 'líbero')", "saídas/jogo", True),
        ("avg_distance_from_goal", "Atuam mais longe da própria baliza", "metros", True),
        ("pass_success_pct", "Melhor eficácia de passe", "% passes certos", True),
        ("long_ball_pct", "Mais dependentes de bola longa", "% bola longa", True),
    ]

    for col, title, unit, descending in categories:
        lines.append(f"\n▸ {title}")
        top = table.sort_values(col, ascending=not descending).head(top_n)
        for rank, (player, row) in enumerate(top.iterrows(), start=1):
            value = row[col]
            lines.append(f"   {rank}. {player:<30} {value:.1f} {unit}  ({row['minutes']:.0f} min jogados)")

    lines.append("\n" + "=" * 60)
    lines.append("Nota: valores baseados na amostra analisada (ver 'minutes' para fiabilidade).")
    return "\n".join(lines)