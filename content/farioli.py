"""Modelo de prioridades do Farioli: quem é o guarda-redes mais parecido com o Diogo Costa?

Duas fases (como num departamento de scouting):

  Fase 1 -- Defesa de remates, época 2025/26 completa, 6 ligas
            (Premier League, La Liga, Serie A, Bundesliga, Championship, Liga Portugal).
            Serve para filtrar a shortlist.
  Fase 2 -- Perfil completo da shortlist: defesa de remates (2025/26) + estilo (2026/27):
            construção, jogo fora da área, cruzamentos e fiabilidade.

Semelhança ponderada:
  Para cada métrica, mede-se a distância ao Diogo Costa em desvios-padrão (z-score) e
  converte-se numa semelhança de 0 a 100% (exp(-distância)). A nota final é a média
  ponderada pelos pesos das PRIORIDADES, que somam 100%.
  Só se penaliza ficar ABAIXO do Diogo Costa naquilo que o Farioli valoriza: um substituto
  que passa mais, sai mais da área ou evita mais golos não é "menos parecido", é melhor.

Uso:
  python content/farioli.py                # tabela + gráficos
  python content/farioli.py --vertical     # gráficos 9:16
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
DADOS = AQUI / "dados"
SAIDA = AQUI / "graficos"
ALVO = "Diogo Costa"
MIN_MINUTOS_2526 = 1800

FUNDO, PAINEL, TEXTO, TEXTO_2, GRELHA = "#0f1420", "#1a2233", "#f2f4f8", "#9aa4b8", "#2a3448"
CORES_BLOCO = {
    "Construção com os pés": "#38bdf8",
    "Defesa de remates": "#22c55e",
    "Jogo fora da área": "#f5b301",
    "Domínio da área": "#f472b6",
    "Fiabilidade": "#a78bfa",
}
ASSINATURA = "@a_tua_conta"

# --------------------------------------------------------------------------
# PRIORIDADES DO FARIOLI (somam 100%). Muda aqui e corre outra vez.
# sentido: "mais" = mais é melhor para o Farioli (ter MAIS do que o DC não penaliza)
#          "menos" = menos é melhor (ter MENOS do que o DC não penaliza)
#          "estilo" = queremos igual, para cima ou para baixo
# Resultado: 100% = iguala ou supera o Diogo Costa em todas as prioridades.
# --------------------------------------------------------------------------
PRIORIDADES = [
    # bloco, métrica, rótulo, peso %, sentido
    ("Construção com os pés", "passes_certos_pct", "Passes certos %", 15, "mais"),
    ("Construção com os pés", "passes_90", "Passes tentados /90 (envolvimento)", 10, "mais"),
    ("Construção com os pés", "bola_longa_pct", "% de passes longos (jogar curto)", 10, "menos"),
    ("Defesa de remates", "golos_evitados_90_2526", "Golos evitados /90 (2025/26)", 25, "mais"),
    ("Defesa de remates", "defesa_pct_2526", "Defesas % (2025/26)", 10, "mais"),
    ("Jogo fora da área", "libero_90", "Ações de líbero /90", 15, "mais"),
    ("Domínio da área", "saidas_altas_90", "Saídas a cruzamentos /90", 10, "mais"),
    ("Fiabilidade", "erros_golo_90", "Erros que deram golo /90", 5, "menos"),
]
assert sum(p[3] for p in PRIORIDADES) == 100, "os pesos têm de somar 100%"


def carregar():
    rem = pd.read_csv(DADOS / "fotmob_defesa_remates_2025_26.csv")
    rem["golos_evitados_90_2526"] = rem.golos_evitados / rem.minutos * 90
    rem["defesa_pct_2526"] = rem.defesas / (rem.defesas + rem.golos_sofridos) * 100
    rem["remates_enq_90_2526"] = (rem.defesas + rem.golos_sofridos) / rem.minutos * 90
    rem = rem[rem.minutos >= MIN_MINUTOS_2526]

    est = pd.read_csv(DADOS / "fotmob_candidatos_estilo_2026_27.csv")
    m = est.minutos
    est["libero_90"] = est.acoes_libero / m * 90
    est["saidas_altas_90"] = est.saidas_altas / m * 90
    est["erros_golo_90"] = est.erros_golo / m * 90
    passes_t = est.passes_certos / (est.passes_certos_pct / 100)
    longos_t = est.passes_longos_certos / (est.passes_longos_certos_pct / 100)
    est["passes_90"] = passes_t / m * 90
    est["bola_longa_pct"] = longos_t / passes_t * 100

    df = est.merge(rem[["jogador", "liga", "minutos", "golos_evitados_90_2526", "defesa_pct_2526",
                        "remates_enq_90_2526"]].rename(columns={"liga": "liga_2526", "minutos": "minutos_2526"}),
                   on="jogador", how="left")
    return rem, df


def escala(serie: pd.Series) -> float:
    """Desvio robusto (MAD); se for 0, usa o desvio-padrão."""
    mad = (serie - serie.median()).abs().median() * 1.4826
    return mad or serie.std(ddof=0) or 1.0


def semelhanca(rem, df):
    alvo = df[df.jogador == ALVO].iloc[0]
    out = df[df.jogador != ALVO].copy()
    blocos = {}
    out["semelhanca"] = 0.0
    for bloco, col, _rot, peso, sentido in PRIORIDADES:
        # a escala da defesa de remates vem das 6 ligas inteiras; a de estilo, da shortlist
        base = rem[col] if col.endswith("_2526") else df[col]
        diff = (out[col] - alvo[col]) / escala(base.dropna())
        if sentido == "mais":
            diff = diff.clip(upper=0)
        elif sentido == "menos":
            diff = diff.clip(lower=0)
        s = np.exp(-diff.abs()) * 100
        out[f"sim_{col}"] = s
        out["semelhanca"] += s * peso / 100
        blocos.setdefault(bloco, []).append((col, peso))
    for bloco, itens in blocos.items():
        tot = sum(p for _, p in itens)
        out[f"bloco_{bloco}"] = sum(out[f"sim_{c}"] * p for c, p in itens) / tot
    return alvo, out.sort_values("semelhanca", ascending=False)


# --------------------------------------------------------------------------
# Gráficos
# --------------------------------------------------------------------------

def _fig(v):
    return plt.figure(figsize=(9, 16) if v else (16, 9), dpi=120, facecolor=FUNDO)


def _rodape(fig):
    fig.text(0.02, 0.015, "Dados: FotMob · defesa de remates 2025/26 · estilo 2026/27 · recolha 2026-11-02",
             color=TEXTO_2, fontsize=10)
    fig.text(0.98, 0.015, ASSINATURA, color=TEXTO_2, fontsize=10, ha="right")


def grafico_prioridades(v):
    fig = _fig(v)
    ax = fig.add_axes([0.1, 0.12, 0.8, 0.12] if not v else [0.08, 0.55, 0.84, 0.06])
    x = 0
    for bloco, cor in CORES_BLOCO.items():
        peso = sum(p[3] for p in PRIORIDADES if p[0] == bloco)
        ax.barh(0, peso, left=x, color=cor, height=1)
        ax.text(x + peso / 2, 0, f"{peso}%", ha="center", va="center", color=FUNDO, fontsize=18,
                fontweight="bold")
        x += peso
    ax.set_xlim(0, 100)
    ax.axis("off")
    fig.text(0.5, 0.92, "O guarda-redes do Farioli: o que pesa mais?", ha="center", color=TEXTO,
             fontsize=28, fontweight="bold")
    y = 0.82
    for bloco, cor in CORES_BLOCO.items():
        fig.text(0.1 if not v else 0.08, y, f"■ {bloco}", color=cor, fontsize=17, fontweight="bold")
        y -= 0.04
        for b, _c, rot, peso, _s in PRIORIDADES:
            if b == bloco:
                fig.text(0.13 if not v else 0.11, y, f"{rot}: {peso}%", color=TEXTO, fontsize=13)
                y -= 0.032
        y -= 0.01
    _rodape(fig)
    nome = "farioli_prioridades" + ("_vertical" if v else "") + ".png"
    fig.savefig(SAIDA / nome, facecolor=FUNDO)
    plt.close(fig)
    print(f"Gráfico guardado em {SAIDA / nome}")


def grafico_ranking(res, v):
    top = res.head(10)
    fig = _fig(v)
    ax = fig.add_axes([0.33, 0.08, 0.6, 0.72] if not v else [0.42, 0.08, 0.52, 0.72])
    ax.set_facecolor(FUNDO)
    blocos = list(CORES_BLOCO)
    for i, (_, r) in enumerate(top.iterrows()):
        y = len(top) - 1 - i
        x = 0
        ax.barh(y, 100, height=0.62, color=PAINEL)
        for b in blocos:
            peso = sum(p[3] for p in PRIORIDADES if p[0] == b)
            w = r[f"bloco_{b}"] * peso / 100
            ax.barh(y, w, left=x, height=0.62, color=CORES_BLOCO[b])
            x += w
        ax.text(x + 1.2, y, f"{r.semelhanca:.0f}%", va="center", color=TEXTO, fontsize=15, fontweight="bold")
        ax.text(-2, y + 0.14, r.jogador, ha="right", va="center", color=TEXTO, fontsize=14)
        ax.text(-2, y - 0.22, f"{r.clube_atual} · {int(r.idade)} anos · {r.valor_fotmob_meur:g} M€",
                ha="right", va="center", color=TEXTO_2, fontsize=10.5)
    ax.set_xlim(0, 110)
    ax.set_ylim(-0.6, len(top) - 0.4)
    ax.axis("off")
    fig.text(0.5, 0.93, "Quem é o Diogo Costa do mercado estrangeiro?", ha="center", color=TEXTO,
             fontsize=28, fontweight="bold")
    fig.text(0.5, 0.885, "Semelhança ponderada pelas prioridades do Farioli · 100% = iguala ou supera o Diogo Costa em tudo",
             ha="center", color=TEXTO_2, fontsize=13)
    xs = np.linspace(0.18, 0.82, len(CORES_BLOCO))
    for xx, (b, c) in zip(xs, CORES_BLOCO.items()):
        fig.text(xx, 0.845, f"■ {b}", ha="center", color=c, fontsize=11.5, fontweight="bold")
    _rodape(fig)
    nome = "farioli_ranking" + ("_vertical" if v else "") + ".png"
    fig.savefig(SAIDA / nome, facecolor=FUNDO)
    plt.close(fig)
    print(f"Gráfico guardado em {SAIDA / nome}")


def grafico_fase1(rem, v):
    fig = _fig(v)
    ax = fig.add_axes([0.08, 0.1, 0.86, 0.7])
    ax.set_facecolor(FUNDO)
    cores_liga = {"Premier League": "#a78bfa", "La Liga": "#f5b301", "Serie A": "#38bdf8",
                  "Bundesliga": "#ef4444", "Championship": "#9aa4b8", "Liga Portugal": "#22c55e"}
    for liga, g in rem.groupby("liga"):
        ax.scatter(g.defesa_pct_2526, g.golos_evitados_90_2526, s=55, alpha=0.75,
                   color=cores_liga.get(liga, TEXTO_2), label=f"{liga} ({len(g)})")
    dc = rem[rem.jogador == ALVO].iloc[0]
    ax.scatter(dc.defesa_pct_2526, dc.golos_evitados_90_2526, s=320, marker="*", color="#ffffff",
               edgecolor="#000", zorder=5)
    ax.annotate("Diogo Costa", (dc.defesa_pct_2526, dc.golos_evitados_90_2526), xytext=(10, -14),
                textcoords="offset points", color=TEXTO, fontsize=13, fontweight="bold")
    for _, r in rem.nlargest(8, "golos_evitados_90_2526").iterrows():
        ax.annotate(r.jogador, (r.defesa_pct_2526, r.golos_evitados_90_2526), xytext=(6, 4),
                    textcoords="offset points", color=TEXTO_2, fontsize=10)
    ax.axhline(0, color=GRELHA, ls="--")
    ax.set_xlabel("Defesas % (2025/26)", color=TEXTO, fontsize=14)
    ax.set_ylabel("Golos evitados por 90 (2025/26)", color=TEXTO, fontsize=14)
    ax.tick_params(colors=TEXTO_2)
    for s in ax.spines.values():
        s.set_color(GRELHA)
    ax.legend(facecolor=PAINEL, edgecolor=GRELHA, labelcolor=TEXTO, loc="lower right", fontsize=10)
    fig.text(0.5, 0.92, "Fase 1: defesa de remates em 6 ligas", ha="center", color=TEXTO, fontsize=28,
             fontweight="bold")
    fig.text(0.5, 0.875, f"{len(rem)} guarda-redes com ≥{MIN_MINUTOS_2526} min em 2025/26",
             ha="center", color=TEXTO_2, fontsize=13)
    _rodape(fig)
    nome = "farioli_fase1" + ("_vertical" if v else "") + ".png"
    fig.savefig(SAIDA / nome, facecolor=FUNDO)
    plt.close(fig)
    print(f"Gráfico guardado em {SAIDA / nome}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vertical", action="store_true")
    a = p.parse_args()
    SAIDA.mkdir(exist_ok=True)
    rem, df = carregar()
    alvo, res = semelhanca(rem, df)

    print("\nPerfil do Diogo Costa:")
    for _b, col, rot, peso, _s in PRIORIDADES:
        pct = ""
        if col.endswith("_2526"):
            pct = f"  (percentil {(rem[col] < alvo[col]).mean() * 100:.0f} em {len(rem)} GR de 6 ligas)"
        print(f"  {rot:<40} {alvo[col]:>7.2f}   peso {peso}%{pct}")

    cols = ["jogador", "clube_atual", "idade", "valor_fotmob_meur", "semelhanca"] + [f"bloco_{b}" for b in CORES_BLOCO]
    with pd.option_context("display.width", 250, "display.float_format", "{:.0f}".format):
        print("\nRanking de semelhança (ponderada pelas prioridades):\n")
        print(res[cols].rename(columns=lambda c: c.replace("bloco_", "")).to_string(index=False))
    with pd.option_context("display.width", 250, "display.float_format", "{:.2f}".format):
        print("\nValores brutos:\n")
        print(pd.concat([df[df.jogador == ALVO], res])[["jogador"] + [p[1] for p in PRIORIDADES]
                                                        + ["remates_enq_90_2526"]].to_string(index=False))

    grafico_prioridades(a.vertical)
    grafico_fase1(rem, a.vertical)
    grafico_ranking(res, a.vertical)


if __name__ == "__main__":
    main()
