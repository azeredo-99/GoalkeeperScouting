"""Análise de guarda-redes com dados atuais (FotMob), para os vídeos.

Lê um CSV no formato de content/dados/fotmob_*.csv (totais da época, copiados
à mão da FotMob) e calcula métricas por 90 minutos e percentagens.

Comandos:

  tabela      Mostra todas as métricas calculadas (para o guião).
  comparar    Gráfico lado a lado de 2+ guarda-redes.
  percentis   Percentil de um guarda-redes contra os pares da mesma liga.
  similares   Ranking dos guarda-redes mais parecidos com um alvo.

Exemplos:

  python content/analise.py tabela --csv content/dados/fotmob_liga_portugal_2025_26.csv
  python content/analise.py comparar --csv content/dados/fotmob_liga_portugal_2025_26.csv \
      --jogadores "Rui Silva" "Kaique Pereira"
  python content/analise.py similares --csv content/dados/fotmob_liga_portugal_2025_26.csv \
      --alvo "Diogo Costa" --perfil qualidade

Usa --vertical para o formato 9:16 (Shorts/Reels/TikTok).
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
SAIDA_PADRAO = AQUI / "graficos"

FUNDO = "#0f1420"
PAINEL = "#1a2233"
TEXTO = "#f2f4f8"
TEXTO_2 = "#9aa4b8"
GRELHA = "#2a3448"
CORES = ["#22c55e", "#f5b301", "#38bdf8", "#f472b6"]
ASSINATURA = "@a_tua_conta"  # muda para o nome da tua conta

# --------------------------------------------------------------------------
# Métricas
# --------------------------------------------------------------------------
# chave: (rótulo no gráfico, formato, maior_é_melhor -- None = é estilo, não "melhor")
METRICAS = {
    "golos_evitados_90": ("Golos evitados /90", "{:+.2f}", True),
    "defesa_pct": ("Defesas %", "{:.1f}%", True),
    "remates_enq_90": ("Remates enquadrados sofridos /90", "{:.2f}", None),
    "golos_sofridos_90": ("Golos sofridos /90", "{:.2f}", False),
    "erros_golo_90": ("Erros que deram golo /90", "{:.2f}", False),
    "libero_90": ("Ações de líbero /90", "{:.2f}", None),
    "saidas_altas_90": ("Saídas a cruzamentos /90", "{:.2f}", None),
    "passes_90": ("Passes tentados /90", "{:.1f}", None),
    "passes_certos_pct": ("Passes certos %", "{:.1f}%", True),
    "bola_longa_pct": ("% de passes que são longos", "{:.1f}%", None),
    "passes_longos_certos_pct": ("Passes longos certos %", "{:.1f}%", True),
}

# Perfis de semelhança: que métricas entram e com que peso.
PERFIS = {
    # Como defende, independentemente de quantos remates sofre.
    "qualidade": {"golos_evitados_90": 2.0, "defesa_pct": 1.0},
    # Em que tipo de equipa joga (muito ou pouco testado).
    "contexto": {"remates_enq_90": 1.0, "golos_sofridos_90": 1.0},
    # Como joga: com os pés, fora da área, nos cruzamentos.
    "estilo": {
        "libero_90": 1.0,
        "saidas_altas_90": 1.0,
        "passes_90": 1.0,
        "passes_certos_pct": 1.0,
        "bola_longa_pct": 1.5,
    },
}
PERFIS["completo"] = {**PERFIS["qualidade"], **PERFIS["estilo"]}


def carregar(csv: str) -> pd.DataFrame:
    df = pd.read_csv(csv)
    m = df.minutos.astype(float)
    p90 = lambda col: df[col].astype(float) / m * 90  # noqa: E731
    df["remates_enq"] = df.defesas + df.golos_sofridos
    df["defesa_pct"] = df.defesas / df.remates_enq * 100
    df["golos_evitados_90"] = p90("golos_evitados")
    df["remates_enq_90"] = p90("remates_enq")
    df["golos_sofridos_90"] = p90("golos_sofridos")
    df["erros_golo_90"] = p90("erros_golo")
    df["libero_90"] = p90("acoes_libero")
    df["saidas_altas_90"] = p90("saidas_altas")
    passes_t = df.passes_certos / (df.passes_certos_pct / 100)
    longos_t = df.passes_longos_certos / (df.passes_longos_certos_pct / 100)
    df["passes_90"] = passes_t / m * 90
    df["bola_longa_pct"] = longos_t / passes_t * 100
    return df


def _achar(df, nome):
    sel = df[df.jogador.str.lower() == nome.lower()]
    if sel.empty:
        sel = df[df.jogador.str.lower().str.contains(nome.lower())]
    if sel.empty:
        raise SystemExit(f"'{nome}' não está no CSV.")
    return sel.iloc[0]


def _percentil(serie: pd.Series, v: float) -> float:
    s = serie.dropna()
    return ((s < v).mean() + (s == v).mean() / 2) * 100


# --------------------------------------------------------------------------
# Gráficos: utilidades
# --------------------------------------------------------------------------

def _figura(vertical):
    return plt.figure(figsize=(9, 16) if vertical else (16, 9), dpi=120, facecolor=FUNDO)


def _cabecalho(fig, titulo, sub, sub2=None):
    fig.text(0.5, 0.92, titulo, ha="center", color=TEXTO, fontsize=30, fontweight="bold")
    fig.text(0.5, 0.875, sub, ha="center", color=TEXTO_2, fontsize=14)
    if sub2:
        fig.text(0.5, 0.845, sub2, ha="center", color=TEXTO_2, fontsize=11, style="italic")


def _rodape(fig, fonte):
    fig.text(0.02, 0.015, f"Dados: {fonte}", color=TEXTO_2, fontsize=11)
    fig.text(0.98, 0.015, ASSINATURA, color=TEXTO_2, fontsize=11, ha="right")


def _guardar(fig, saida, nome):
    Path(saida).mkdir(parents=True, exist_ok=True)
    caminho = Path(saida) / nome
    fig.savefig(caminho, facecolor=FUNDO)
    plt.close(fig)
    print(f"Gráfico guardado em {caminho}")


def _slug(t):
    t = "".join(c.lower() if c.isalnum() else "_" for c in t)
    return "_".join(p for p in t.split("_") if p)


def _fonte(df):
    return f"FotMob · Liga Portugal {df.epoca.iloc[0]} · recolha {df.data_recolha.iloc[0]}"


# --------------------------------------------------------------------------
# Comandos
# --------------------------------------------------------------------------

def tabela(args):
    df = carregar(args.csv)
    df = df[df.minutos >= args.min_minutos]
    cols = ["jogador", "clube", "minutos"] + [c for c in METRICAS if df[c].notna().any()]
    with pd.option_context("display.width", 250, "display.max_columns", 50,
                           "display.float_format", "{:.2f}".format):
        print(df[cols].sort_values(args.ordenar, ascending=False).to_string(index=False))


def comparar(args):
    df = carregar(args.csv)
    linhas = [_achar(df, n) for n in args.jogadores]
    metricas = [k for k in METRICAS if all(not pd.isna(r[k]) for r in linhas)]
    if not metricas:
        raise SystemExit("Nenhuma métrica disponível para todos.")

    fig = _figura(args.vertical)
    ax = fig.add_axes([0.38 if args.vertical else 0.32, 0.07, 0.5 if args.vertical else 0.58, 0.68])
    ax.set_facecolor(FUNDO)
    n, k = len(metricas), len(linhas)
    h = 0.8 / k
    for i, key in enumerate(metricas):
        rot, fmt, melhor_alto = METRICAS[key]
        vals = [float(r[key]) for r in linhas]
        esc = max(abs(v) for v in vals) or 1
        melhor = None if melhor_alto is None else (max(vals) if melhor_alto else min(vals))
        y0 = n - 1 - i
        for j, v in enumerate(vals):
            y = y0 + 0.4 - (j + 0.5) * h
            w = abs(v) / esc
            ax.barh(y, 1, height=h * 0.85, color=PAINEL)
            ax.barh(y, w, height=h * 0.85, color=CORES[j],
                    alpha=1 if (melhor is None or v == melhor) else 0.5)
            ax.text(w + 0.015, y, fmt.format(v), va="center", color=TEXTO, fontsize=13,
                    fontweight="bold" if v == melhor else "normal")
        ax.text(-0.02, y0, rot + ("" if melhor_alto is not None else "  ◦"), va="center",
                ha="right", color=TEXTO, fontsize=13)
    ax.set_xlim(0, 1.25)
    ax.set_ylim(-0.6, n - 0.4)
    ax.axis("off")

    titulo = args.titulo or " vs ".join(r.jogador for r in linhas)
    sub = " · ".join(f"{r.jogador} ({r.clube}, {int(r.minutos)} min)" for r in linhas)
    _cabecalho(fig, titulo, sub, "◦ = métrica de estilo/contexto: nem mais nem menos é 'melhor'")
    for j, r in enumerate(linhas):
        fig.text(0.5 + (j - (k - 1) / 2) * 0.2, 0.80, f"■ {r.jogador}", ha="center",
                 color=CORES[j], fontsize=15, fontweight="bold")
    _rodape(fig, _fonte(df))
    _guardar(fig, args.saida, f"comparar_{_slug('_'.join(args.jogadores))}_{_slug(str(df.epoca.iloc[0]))}"
             + ("_vertical" if args.vertical else "") + ".png")


def percentis(args):
    df = carregar(args.csv)
    alvo = _achar(df, args.jogador)
    pares = df[df.minutos >= args.min_minutos]
    linhas = []
    for key, (rot, fmt, melhor_alto) in METRICAS.items():
        if pd.isna(alvo[key]) or pares[key].notna().sum() < 5:
            continue
        pct = _percentil(pares[key], alvo[key])
        if melhor_alto is False:  # inverte: a barra mede sempre "quão bom", não "quão alto"
            pct, rot = 100 - pct, rot + " (menos = melhor)"
        linhas.append((rot, fmt.format(alvo[key]), pct, melhor_alto, pares[key].notna().sum()))
    fig = _figura(args.vertical)
    ax = fig.add_axes([0.45 if args.vertical else 0.36, 0.08, 0.45 if args.vertical else 0.52, 0.68])
    ax.set_facecolor(FUNDO)
    for i, (rot, val, pct, melhor_alto, npares) in enumerate(linhas):
        y = len(linhas) - 1 - i
        if melhor_alto is None:
            cor = CORES[2]
        else:
            cor = CORES[0] if pct >= 66 else (CORES[1] if pct >= 33 else "#ef4444")
        ax.barh(y, 100, height=0.6, color=PAINEL)
        ax.barh(y, pct, height=0.6, color=cor)
        ax.text(pct + 1.5, y, f"{pct:.0f}", va="center", color=TEXTO, fontsize=15, fontweight="bold")
        ax.text(-3, y + 0.13, rot, va="center", ha="right", color=TEXTO, fontsize=13)
        ax.text(-3, y - 0.22, f"{val}  (n={npares})", va="center", ha="right", color=TEXTO_2, fontsize=11)
    for x in (25, 50, 75):
        ax.axvline(x, color=GRELHA, ls="--", lw=1, zorder=0)
    ax.set_xlim(0, 108)
    ax.set_ylim(-0.6, len(linhas) - 0.4)
    ax.axis("off")
    _cabecalho(fig, args.titulo or f"{alvo.jogador} · {alvo.clube}",
               f"Percentil vs guarda-redes da Liga Portugal {alvo.epoca} (≥{args.min_minutos} min) · {int(alvo.minutos)} min",
               "verde = bom · vermelho = fraco · azul = estilo (nem bom nem mau)")
    _rodape(fig, _fonte(df))
    _guardar(fig, args.saida, f"percentis_{_slug(alvo.jogador)}_{_slug(str(alvo.epoca))}"
             + ("_vertical" if args.vertical else "") + ".png")


def calcular_similares(df, alvo_nome, perfil, min_minutos):
    pesos = PERFIS[perfil]
    cols = list(pesos)
    alvo = _achar(df, alvo_nome)
    pool = df[(df.minutos >= min_minutos) | (df.jogador == alvo.jogador)].dropna(subset=cols).copy()
    if alvo.jogador not in set(pool.jogador):
        raise SystemExit(f"{alvo.jogador} não tem dados para o perfil '{perfil}'.")
    # z-scores robustos (mediana / desvio absoluto mediano) -> um extremo não distorce a escala
    z = pd.DataFrame(index=pool.index)
    for c in cols:
        med = pool[c].median()
        mad = (pool[c] - med).abs().median() * 1.4826 or pool[c].std(ddof=0) or 1
        z[c] = (pool[c] - med) / mad
    w = np.array([pesos[c] for c in cols])
    za = z.loc[pool.jogador == alvo.jogador].iloc[0].values
    dist = np.sqrt((((z.values - za) ** 2) * w).sum(axis=1) / w.sum())
    pool["distancia"] = dist
    pool["semelhanca"] = 100 * np.exp(-dist / 1.5)
    out = pool[pool.jogador != alvo.jogador].sort_values("semelhanca", ascending=False)
    return alvo, out, cols


def similares(args):
    df = carregar(args.csv)
    alvo, res, cols = calcular_similares(df, args.alvo, args.perfil, args.min_minutos)
    top = res.head(args.top)
    print(f"\nMais parecidos com {alvo.jogador} (perfil '{args.perfil}': {', '.join(cols)})"
          f" · {len(res)} candidatos\n")
    mostrar = ["jogador", "clube", "minutos", "semelhanca"] + cols
    with pd.option_context("display.width", 250, "display.float_format", "{:.2f}".format):
        print(pd.concat([df[df.jogador == alvo.jogador].assign(semelhanca=100.0)[mostrar], top[mostrar]])
              .to_string(index=False))

    fig = _figura(args.vertical)
    ax = fig.add_axes([0.35 if not args.vertical else 0.45, 0.08, 0.55 if not args.vertical else 0.45, 0.68])
    ax.set_facecolor(FUNDO)
    for i, (_, r) in enumerate(top.iterrows()):
        y = len(top) - 1 - i
        ax.barh(y, 100, height=0.6, color=PAINEL)
        ax.barh(y, r.semelhanca, height=0.6, color=CORES[0] if i == 0 else CORES[2])
        ax.text(r.semelhanca + 1.5, y, f"{r.semelhanca:.0f}%", va="center", color=TEXTO,
                fontsize=15, fontweight="bold")
        ax.text(-3, y + 0.13, r.jogador, va="center", ha="right", color=TEXTO, fontsize=14)
        ax.text(-3, y - 0.22, f"{r.clube} · {int(r.minutos)} min", va="center", ha="right",
                color=TEXTO_2, fontsize=11)
    ax.set_xlim(0, 112)
    ax.set_ylim(-0.6, len(top) - 0.4)
    ax.axis("off")
    _cabecalho(fig, args.titulo or f"Quem é o mais parecido com {alvo.jogador}?",
               f"Perfil '{args.perfil}': " + ", ".join(METRICAS[c][0] for c in cols),
               "Semelhança = distância entre perfis normalizados (100% = perfil igual). Não é uma nota de qualidade.")
    _rodape(fig, _fonte(df))
    _guardar(fig, args.saida, f"similares_{_slug(alvo.jogador)}_{args.perfil}_{_slug(str(alvo.epoca))}"
             + ("_vertical" if args.vertical else "") + ".png")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def base(sp, func):
        sp.add_argument("--csv", required=True)
        sp.add_argument("--min-minutos", type=int, default=900)
        sp.add_argument("--vertical", action="store_true")
        sp.add_argument("--saida", default=str(SAIDA_PADRAO))
        sp.add_argument("--titulo")
        sp.set_defaults(func=func)

    t = sub.add_parser("tabela")
    base(t, tabela)
    t.add_argument("--ordenar", default="golos_evitados_90")
    c = sub.add_parser("comparar")
    base(c, comparar)
    c.add_argument("--jogadores", nargs="+", required=True)
    pc = sub.add_parser("percentis")
    base(pc, percentis)
    pc.add_argument("--jogador", required=True)
    s = sub.add_parser("similares")
    base(s, similares)
    s.add_argument("--alvo", required=True)
    s.add_argument("--perfil", choices=list(PERFIS), default="qualidade")
    s.add_argument("--top", type=int, default=5)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
