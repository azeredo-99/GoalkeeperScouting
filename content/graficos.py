"""Gráficos prontos para vídeo (16:9 ou 9:16) para a série de análise de guarda-redes.

Três comandos:

  comparar      Compara 2+ guarda-redes a partir de um CSV preenchido à mão
                (ex.: Rui Silva vs Kaique com dados do FotMob/Sofascore).
  percentis     Percentis de um guarda-redes contra os pares da mesma
                competição/época, com os dados StatsBomb do projeto.
  shortlist     Dispersão defesa% vs remates enquadrados/90 nas 5 grandes ligas
                2024/25 (FBref), a destacar os guarda-redes mais jovens.

Exemplos:

  python content/graficos.py comparar \
      --csv content/dados/liga_portugal_manual.csv \
      --epoca 2025/26 --jogadores "Rui Silva" "Kaique"

  python content/graficos.py percentis --jogador "Diogo Meireles Costa" \
      --competicao 55 --epoca-id 282 --titulo "Diogo Costa · Euro 2024"

  python content/graficos.py shortlist --nascido-depois 2000

Usa --vertical para o formato Shorts/Reels/TikTok (1080x1920).
Os PNG ficam em content/graficos/ (ou --saida).
"""

from __future__ import annotations

import argparse
import glob
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
SAIDA_PADRAO = RAIZ / "content" / "graficos"
DEMO_CSV = RAIZ / "data" / "demo" / "gk_performances.csv"
FBREF_DIR = RAIZ / "data" / "raw" / "fbref" / "2024-25"

# Paleta "transmissão": fundo escuro, texto claro, duas cores fortes.
FUNDO = "#0f1420"
PAINEL = "#1a2233"
TEXTO = "#f2f4f8"
TEXTO_2 = "#9aa4b8"
GRELHA = "#2a3448"
CORES = ["#22c55e", "#f5b301", "#38bdf8", "#f472b6"]

ASSINATURA = "@a_tua_conta"  # muda para o nome da tua conta


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def _figura(vertical: bool):
    tamanho = (9, 16) if vertical else (16, 9)
    fig = plt.figure(figsize=tamanho, dpi=120, facecolor=FUNDO)
    return fig


def _rodape(fig, fonte: str):
    fig.text(0.02, 0.015, f"Dados: {fonte}", color=TEXTO_2, fontsize=11, ha="left")
    fig.text(0.98, 0.015, ASSINATURA, color=TEXTO_2, fontsize=11, ha="right")


def _guardar(fig, saida: Path, nome: str) -> Path:
    saida.mkdir(parents=True, exist_ok=True)
    caminho = saida / nome
    fig.savefig(caminho, facecolor=FUNDO)
    plt.close(fig)
    print(f"Gráfico guardado em {caminho}")
    return caminho


def _slug(texto: str) -> str:
    keep = "".join(c.lower() if c.isalnum() else "_" for c in texto)
    return "_".join(p for p in keep.split("_") if p)


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return math.nan
    return v


def _div(a, b, mult=1.0):
    a, b = _num(a), _num(b)
    if math.isnan(a) or math.isnan(b) or b == 0:
        return math.nan
    return a / b * mult


# --------------------------------------------------------------------------
# 1) comparar -- CSV manual
# --------------------------------------------------------------------------

# (nome no gráfico, função que calcula a partir da linha, formato, maior_é_melhor)
METRICAS_MANUAIS = [
    ("Defesas %", lambda r: _div(r.defesas, r.remates_enquadrados_contra, 100), "{:.1f}%", True),
    ("Golos sofridos /90", lambda r: _div(r.golos_sofridos, r.minutos, 90), "{:.2f}", False),
    ("Golos evitados /90\n(xGOT − golos)", lambda r: _div(_num(r.xgot_contra) - _num(r.golos_sofridos), r.minutos, 90), "{:+.2f}", True),
    ("Jogos sem sofrer %", lambda r: _div(r.jogos_sem_sofrer, r.jogos, 100), "{:.0f}%", True),
    ("Penáltis defendidos", lambda r: _num(r.penaltis_defendidos), "{:.0f}", True),
    ("Passes certos %", lambda r: _div(r.passes_certos, r.passes_tentados, 100), "{:.1f}%", True),
    ("Passes longos certos %", lambda r: _div(r.passes_longos_certos, r.passes_longos_tentados, 100), "{:.1f}%", True),
    ("Saídas a cruzamentos /90", lambda r: _div(r.saidas_cruzamento, r.minutos, 90), "{:.2f}", True),
    ("Ações fora da área /90", lambda r: _div(r.acoes_fora_area, r.minutos, 90), "{:.2f}", True),
]


def comparar(args):
    df = pd.read_csv(args.csv)
    if args.epoca:
        df = df[df.epoca == args.epoca]
    linhas = []
    for nome in args.jogadores:
        sel = df[df.jogador.str.lower() == nome.lower()]
        if sel.empty:
            raise SystemExit(f"'{nome}' não encontrado em {args.csv} (época {args.epoca}).")
        linhas.append(sel.iloc[0])

    # Só mostra métricas com valor para TODOS os jogadores -- nunca inventa zeros.
    linhas_metricas = []
    for rotulo, f, fmt, melhor_alto in METRICAS_MANUAIS:
        valores = [f(r) for r in linhas]
        if any(math.isnan(v) for v in valores):
            continue
        linhas_metricas.append((rotulo, valores, fmt, melhor_alto))
    if not linhas_metricas:
        raise SystemExit("Nenhuma métrica com dados para todos os jogadores. Preenche o CSV.")

    fig = _figura(args.vertical)
    topo = 0.80 if args.vertical else 0.78
    ax = fig.add_axes([0.08, 0.08, 0.84, topo - 0.08])
    ax.set_facecolor(FUNDO)

    n = len(linhas_metricas)
    k = len(linhas)
    altura = 0.8 / k
    for i, (rotulo, valores, fmt, melhor_alto) in enumerate(linhas_metricas):
        y0 = n - 1 - i
        escala = max(abs(v) for v in valores) or 1
        melhor = max(valores) if melhor_alto else min(valores)
        for j, v in enumerate(valores):
            y = y0 + 0.4 - (j + 0.5) * altura
            largura = abs(v) / escala
            ax.barh(y, 1, height=altura * 0.85, color=PAINEL, zorder=1)
            ax.barh(y, largura, height=altura * 0.85, color=CORES[j % len(CORES)],
                    alpha=1.0 if v == melhor else 0.55, zorder=2)
            ax.text(min(largura, 1) + 0.015, y, fmt.format(v), va="center",
                    color=TEXTO, fontsize=14, fontweight="bold" if v == melhor else "normal")
        ax.text(-0.02, y0, rotulo, va="center", ha="right", color=TEXTO, fontsize=14)

    ax.set_xlim(0, 1.2)
    ax.set_ylim(-0.6, n - 0.4)
    ax.axis("off")
    fig.subplots_adjust(left=0.3)
    ax.set_position([0.30 if not args.vertical else 0.38, 0.08, 0.62 if not args.vertical else 0.55, topo - 0.08])

    titulo = args.titulo or " vs ".join(r.jogador for r in linhas)
    fig.text(0.5, 0.92, titulo, ha="center", color=TEXTO, fontsize=30, fontweight="bold")
    sub = " · ".join(
        f"{r.jogador} ({r.clube}, {int(_num(r.minutos))} min)" for r in linhas
    )
    fig.text(0.5, 0.865, f"{args.epoca or ''}  {linhas[0].competicao}", ha="center", color=TEXTO_2, fontsize=15)
    fig.text(0.5, 0.83, sub, ha="center", color=TEXTO_2, fontsize=13)
    # legenda de cores
    for j, r in enumerate(linhas):
        fig.text(0.5 + (j - (k - 1) / 2) * 0.18, 0.80 if not args.vertical else 0.815, f"■ {r.jogador}",
                 ha="center", color=CORES[j % len(CORES)], fontsize=15, fontweight="bold")
    _rodape(fig, args.fonte)
    nome = f"comparar_{_slug('_'.join(args.jogadores))}_{_slug(args.epoca or 'todas')}"
    nome += "_vertical.png" if args.vertical else ".png"
    return _guardar(fig, Path(args.saida), nome)


# --------------------------------------------------------------------------
# 2) percentis -- dados StatsBomb do projeto
# --------------------------------------------------------------------------

METRICAS_SB = [
    ("save_pct", "Defesas %", "{:.1f}%"),
    ("pass_success_pct", "Passes certos %", "{:.1f}%"),
    ("avg_pass_length", "Comprimento médio do passe (m)", "{:.1f}"),
    ("long_ball_pct", "Bolas longas %", "{:.1f}%"),
    ("sweeper_actions_p90", "Ações de líbero /90", "{:.2f}"),
    ("avg_distance_from_goal", "Distância média dessas ações (m)", "{:.1f}"),
]


def percentis(args):
    df = pd.read_csv(DEMO_CSV)
    pares = df[(df.competition_id == args.competicao) & (df.season_id == args.epoca_id)
               & (df.source == "statsbomb")]
    alvo = pares[pares.player_name == args.jogador]
    if alvo.empty:
        raise SystemExit(f"'{args.jogador}' não está nessa competição/época.")
    pares = pares[pares.minutes >= args.min_minutos]
    alvo = alvo.iloc[0]

    fig = _figura(args.vertical)
    ax = fig.add_axes([0.36 if not args.vertical else 0.45, 0.10, 0.52 if not args.vertical else 0.45, 0.66])
    ax.set_facecolor(FUNDO)

    linhas = []
    for col, rotulo, fmt in METRICAS_SB:
        v = alvo[col]
        serie = pares[col].dropna()
        if pd.isna(v) or serie.empty:
            continue
        pct = (serie < v).mean() * 100 + (serie == v).mean() * 50
        linhas.append((rotulo, v, fmt, pct))

    for i, (rotulo, v, fmt, pct) in enumerate(linhas):
        y = len(linhas) - 1 - i
        cor = CORES[0] if pct >= 66 else (CORES[1] if pct >= 33 else "#ef4444")
        ax.barh(y, 100, height=0.6, color=PAINEL)
        ax.barh(y, pct, height=0.6, color=cor)
        ax.text(pct + 1.5, y, f"{pct:.0f}", va="center", color=TEXTO, fontsize=15, fontweight="bold")
        ax.text(-3, y + 0.12, rotulo, va="center", ha="right", color=TEXTO, fontsize=14)
        ax.text(-3, y - 0.22, fmt.format(v), va="center", ha="right", color=TEXTO_2, fontsize=12)
    for x in (25, 50, 75):
        ax.axvline(x, color=GRELHA, lw=1, zorder=0, ls="--")
    ax.set_xlim(0, 108)
    ax.set_ylim(-0.6, len(linhas) - 0.4)
    ax.axis("off")

    titulo = args.titulo or args.jogador
    fig.text(0.5, 0.90, titulo, ha="center", color=TEXTO, fontsize=30, fontweight="bold")
    fig.text(0.5, 0.845,
             f"Percentil vs {len(pares)} guarda-redes da mesma competição (≥{args.min_minutos} min) · "
             f"{int(alvo.minutes)} min jogados",
             ha="center", color=TEXTO_2, fontsize=13)
    fig.text(0.5, 0.81, "Percentil alto = valor mais alto que os pares (não é 'melhor' em todas as métricas)",
             ha="center", color=TEXTO_2, fontsize=11, style="italic")
    _rodape(fig, "StatsBomb Open Data")
    nome = f"percentis_{_slug(titulo)}" + ("_vertical.png" if args.vertical else ".png")
    return _guardar(fig, Path(args.saida), nome)


# --------------------------------------------------------------------------
# 3) shortlist -- FBref 2024/25
# --------------------------------------------------------------------------

def _carregar_fbref() -> pd.DataFrame:
    partes = []
    for f in sorted(glob.glob(str(FBREF_DIR / "*_keeper.csv"))):
        r = pd.read_csv(f, header=[0, 1, 2])
        r.columns = [c[2] if "Unnamed" not in c[2] else (c[1] if "Unnamed" not in c[1] else c[0])
                     for c in r.columns]
        partes.append(r.loc[:, ~r.columns.duplicated()])
    return pd.concat(partes, ignore_index=True)


def shortlist(args):
    d = _carregar_fbref()
    d = d[d.Min >= args.min_minutos].copy()
    d["sota90"] = d.SoTA / d["90s"]
    jovens = d[d.born >= args.nascido_depois]

    fig = _figura(args.vertical)
    ax = fig.add_axes([0.08, 0.10, 0.86, 0.68])
    ax.set_facecolor(FUNDO)
    ax.scatter(d["Save%"], d.sota90, s=60, color=TEXTO_2, alpha=0.35, label="Restantes")
    ax.scatter(jovens["Save%"], jovens.sota90, s=140, color=CORES[0], edgecolor=TEXTO,
               label=f"Nascidos em {args.nascido_depois} ou depois")
    for _, r in jovens.iterrows():
        ax.annotate(f"{r.player} ({r.team})", (r["Save%"], r.sota90), xytext=(8, 6),
                    textcoords="offset points", color=TEXTO, fontsize=11)
    ax.axvline(d["Save%"].median(), color=GRELHA, ls="--")
    ax.axhline(d.sota90.median(), color=GRELHA, ls="--")
    ax.set_xlabel("Defesas % (remates enquadrados)", color=TEXTO, fontsize=14)
    ax.set_ylabel("Remates enquadrados sofridos /90", color=TEXTO, fontsize=14)
    ax.tick_params(colors=TEXTO_2)
    for s in ax.spines.values():
        s.set_color(GRELHA)
    ax.legend(facecolor=PAINEL, edgecolor=GRELHA, labelcolor=TEXTO, loc="upper left")

    fig.text(0.5, 0.90, args.titulo, ha="center", color=TEXTO, fontsize=28, fontweight="bold")
    fig.text(0.5, 0.85, f"5 grandes ligas 2024/25 · ≥{args.min_minutos} min · {len(d)} guarda-redes",
             ha="center", color=TEXTO_2, fontsize=13)
    _rodape(fig, "FBref (exportação única 2024/25)")
    nome = f"shortlist_{args.nascido_depois}" + ("_vertical.png" if args.vertical else ".png")
    return _guardar(fig, Path(args.saida), nome)


# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def comuns(sp):
        sp.add_argument("--vertical", action="store_true", help="formato 9:16 (Shorts/Reels)")
        sp.add_argument("--saida", default=str(SAIDA_PADRAO))
        sp.add_argument("--titulo")

    c = sub.add_parser("comparar")
    c.add_argument("--csv", required=True)
    c.add_argument("--jogadores", nargs="+", required=True)
    c.add_argument("--epoca")
    c.add_argument("--fonte", default="FotMob / Sofascore (recolha manual)")
    comuns(c)
    c.set_defaults(func=comparar)

    pc = sub.add_parser("percentis")
    pc.add_argument("--jogador", required=True)
    pc.add_argument("--competicao", type=int, required=True)
    pc.add_argument("--epoca-id", type=int, required=True)
    pc.add_argument("--min-minutos", type=int, default=270)
    comuns(pc)
    pc.set_defaults(func=percentis)

    s = sub.add_parser("shortlist")
    s.add_argument("--nascido-depois", type=int, default=2000)
    s.add_argument("--min-minutos", type=int, default=1800)
    comuns(s)
    s.set_defaults(func=shortlist, titulo=None)

    args = p.parse_args()
    if args.cmd == "shortlist" and not args.titulo:
        args.titulo = "Eficácia vs volume: guarda-redes jovens"
    args.func(args)


if __name__ == "__main__":
    main()
