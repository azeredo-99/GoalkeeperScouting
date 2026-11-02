# Conteúdo: série de vídeos de análise de guarda-redes

Material para os vídeos do portfólio, construído sobre os dados deste projeto.

| Pasta | O quê |
|---|---|
| `guioes/` | Guiões prontos a gravar |
| `graficos.py` | Gera gráficos 16:9 (YouTube) ou 9:16 (`--vertical`, para Shorts/Reels) |
| `dados/` | CSVs para preencher **à mão** com FotMob/Sofascore (sem scraping) |
| `graficos/` | PNGs gerados |

## Vídeos
1. [Os números mentem? Rui Silva vs Kaique](guioes/01_os_numeros_mentem_rui_silva_vs_kaique.md)
2. [Scouting: substituto para o Diogo Costa](guioes/02_scouting_substituto_diogo_costa.md)

## Gráficos
```bash
pip install -r requirements.txt   # só precisa de pandas + matplotlib
python content/graficos.py --help
```
Antes de publicar, muda `ASSINATURA` em `graficos.py` para o nome da tua conta.

Regra de sempre (a mesma do projeto): **nenhuma métrica inventada**. Se um valor faltar para um dos jogadores, essa métrica não aparece no gráfico.
