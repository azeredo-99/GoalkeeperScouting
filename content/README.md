# Conteúdo: série de vídeos de análise de guarda-redes

Análises com **dados atuais da FotMob** (Liga Portugal 2025/26 e 2026/27), recolhidos à mão, página a página. Não usa os dados antigos do projeto.

| Pasta | O quê |
|---|---|
| `guioes/` | Guiões prontos a gravar |
| `analise.py` | Métricas, percentis, comparações e semelhança + gráficos 16:9 ou 9:16 (`--vertical`) |
| `dados/` | CSVs com os totais da época copiados da FotMob (com fonte e data da recolha) |
| `graficos/` | PNGs gerados |

## Vídeos
1. [Os números mentem? Rui Silva vs Kaique](guioes/01_os_numeros_mentem_rui_silva_vs_kaique.md)
2. [Scouting: substituto para o Diogo Costa (Liga Portugal)](guioes/02_scouting_substituto_diogo_costa.md)
3. [O guarda-redes do Farioli no mercado estrangeiro](guioes/03_farioli_mercado_estrangeiro.md): modelo de prioridades (`farioli.py`)

## Métricas
Calculadas a partir dos totais da FotMob:
- **Golos evitados /90**: (xGOT contra − golos sofridos) por 90 min. Mede a qualidade do guarda-redes descontando a dificuldade dos remates.
- **Defesas %**: defesas ÷ (defesas + golos sofridos)
- **Remates enquadrados sofridos /90**: o contexto (quanto a equipa o deixa ser testado)
- **Ações de líbero /90**, **saídas a cruzamentos /90**: o estilo fora da linha de golo
- **Passes /90**, **passes certos %**, **% de passes que são longos**: o estilo com os pés

## Semelhança
`similares` normaliza cada métrica (z-score robusto: mediana e desvio absoluto mediano), calcula a distância ponderada ao alvo e converte-a em 0–100% (100% = perfil igual). Perfis disponíveis:
`qualidade`, `contexto`, `estilo` e `completo`. **Não é uma nota de qualidade**, só mede quão parecido é o perfil.

```bash
pip install pandas numpy matplotlib
python content/analise.py --help
```
Antes de publicar, muda `ASSINATURA` em `analise.py` para o nome da tua conta.

## Notas sobre os dados
- Em 2025/26, os minutos marcados `minutos_estimados=sim` foram calculados como defesas ÷ (defesas por 90) × 90, a partir dos rankings da FotMob (erro de ±1–2%).
- Os valores de golos evitados vêm dos rankings da liga. Na página individual de alguns jogadores, a FotMob mostra valores diferentes, por isso usa sempre a mesma fonte para todos.
- 2026/27 tem poucas jornadas: usa esses dados para o estilo, não para conclusões de rendimento.
