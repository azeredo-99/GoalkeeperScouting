# Se o Diogo Costa sair: o guarda-redes do Farioli no mercado estrangeiro

**Formato:** "Scouting: substituto para o clube X" (versão internacional) · **Duração alvo:** 10–12 min
**Modelo:** `content/farioli.py` · **Dados:** FotMob, recolhidos a 2026-11-02
- **Fase 1 (defesa de remates):** época 2025/26 completa, 113 guarda-redes com ≥1800 min em 6 ligas (Premier League, La Liga, Serie A, Bundesliga, Championship, Liga Portugal) → `dados/fotmob_defesa_remates_2025_26.csv`
- **Fase 2 (estilo):** 2026/27 (7–13 jogos por guarda-redes), shortlist de 13 → `dados/fotmob_candidatos_estilo_2026_27.csv`

---

## 1. O que o Farioli quer de um guarda-redes (o esquema de prioridades)

**Porquê estas prioridades:**
- O próprio Farioli disse, sobre o Diogo Costa: *"Preferimos vê-lo a usar os pés na construção"*. Por isso, a **construção** é a prioridade n.º 1, a par da defesa.
- O Farioli começou a carreira como **treinador de guarda-redes** e as equipas dele (Nice, Ajax, Porto) constroem desde trás e defendem com a linha subida `[CONFIRMAR o percurso]`. Uma linha alta exige um guarda-redes que **saia da área** para cobrir o espaço nas costas.
- **Defender continua a ser o essencial**, por isso pesa tanto como a construção.

| Bloco | Peso | Métricas (peso) | O que se pede |
|---|---|---|---|
| **Construção com os pés** | **35%** | Passes certos % (15) · Passes tentados /90 (10) · % de passes longos (10) | Seguro, envolvido, a jogar curto |
| **Defesa de remates** | **35%** | Golos evitados /90 (25) · Defesas % (10) | Evitar golos acima do esperado |
| **Jogo fora da área** | **15%** | Ações de líbero /90 | Cobrir a profundidade da linha alta |
| **Domínio da área** | **10%** | Saídas a cruzamentos /90 | Sair aos cruzamentos |
| **Fiabilidade** | **5%** | Erros que deram golo /90 | Não comprometer |
| **Total** | **100%** | | |

Os pesos são uma **opinião de analista**, assumida como tal no vídeo. O modelo deixa mudá-los no topo de `farioli.py` e correr outra vez, o que dá um bom momento de vídeo: "se o Farioli valorizasse X, o ranking mudava assim".

## 2. Os valores do Diogo Costa

| Métrica | Diogo Costa | Contexto |
|---|---|---|
| Defesas % (2025/26) | **80,0%** | Percentil **99** entre 113 guarda-redes de 6 ligas |
| Golos evitados /90 (2025/26) | +0,05 | Percentil **49** (exatamente na média) |
| Remates enquadrados sofridos /90 | 2,38 | O menos testado de todos |
| Passes certos % (2026/27) | 81,8% | Só o Nübel e o Murić estão ao nível dele |
| Passes /90 | 30,2 | |
| % de passes longos | 28,8% | **O que joga mais curto** da shortlist |
| Ações de líbero /90 | 0,10 | Baixo (1 ação em 10 jogos) |
| Saídas a cruzamentos /90 | 0,60 | |

**A leitura:** o que torna o Diogo Costa difícil de substituir **não é a defesa de remates**: vários guarda-redes estrangeiros evitam mais golos do que ele. **É a construção.** Quase nenhum guarda-redes junta 80%+ de passes certos e menos de 30% de bolas longas.

## 3. Como funciona a semelhança

Para cada métrica, mede-se quanto o candidato fica **abaixo** do Diogo Costa, em desvios-padrão, e isso converte-se em 0–100%. A nota final é a média ponderada pelos pesos acima.
**Só se penaliza ficar abaixo:** um guarda-redes que evita mais golos ou sai mais da área do que o Diogo Costa não é "menos parecido", é melhor no que o Farioli quer. **100% = iguala ou supera o Diogo Costa em todas as prioridades.**

## 4. Resultados

| # | Guarda-redes | Clube (agora) | Idade | Valor FotMob | **Semelhança** | Construção | Defesa | Notas |
|---|---|---|---|---|---|---|---|---|
| 1 | **Alexander Nübel** | Beşiktaş | 30 | 12 M€ | **88%** | 94 | 73 | 2.º em golos evitados nas 6 ligas em 2025/26 (Estugarda); 82,6% de passes certos |
| 2 | **Arijanet Murić** | Sassuolo | 27 | 5 M€ | **81%** | 83 | 76 | Constrói como o Diogo Costa e domina a área. ⚠️ 3 erros que deram golo em 7 jogos este ano |
| 3 | Maduka Okoye | Udinese | 27 | 10 M€ | 71% | 44 | 75 | Defende bem; joga mais longo |
| 4 | Bart Verbruggen | Brighton | 24 | 48 M€ | 71% | 55 | 73 | O mais completo dos jovens, mas o preço é proibitivo |
| 5 | Mio Backhaus | Freiburg | 22 | 12 M€ | 71% | 54 | 72 | O mais jovem; 2 erros este ano |
| 6 | Leo Román | Deportivo da Corunha | 26 | 8,4 M€ | 71% | 51 | 72 | Muito envolvido na construção (37,6 passes /90) |
| 7 | Marco Carnesecchi | Atalanta | 26 | 29 M€ | 70% | 42 | **83** | O melhor da shortlist a defender; joga longo |

Fora do top 7: Viktor Johansson (69%), Nikola Vasilj (68%, agora na Arábia Saudita), Carl Rushworth (67%), Moritz Nicolas (65%), Radek Vítek (62%), Jacob Widell Zetterström (61%).

**Fora da análise de propósito:** os guarda-redes que estão em clubes inalcançáveis para o Porto (Joan García, Maignan, Donnarumma, Raya, Courtois, Kobel, etc.) e o Daniel Batz, que lidera a fase 1 mas tem 35 anos. Não escondas isto no vídeo: explica que a fase 1 os mostra e porque é que saem.

### A conclusão para o vídeo
- **Mais parecido:** Nübel (88%). Tem experiência, constrói como o Diogo Costa e evita muitos golos. Contra: 30 anos e pouco valor de revenda (não encaixa no modelo de negócio do Porto).
- **Melhor relação perfil/preço:** Murić (81%, 5 M€). Mas o vídeo tem de olhar para os 3 erros desta época.
- **Aposta de futuro:** Backhaus (22 anos) ou Leo Román (26), ambos nos 71% e com margem para crescer na construção.

---

## 5. Guião resumido

**0:00 · Gancho**
> "O Diogo Costa teve a melhor percentagem de defesas de 113 guarda-redes em 6 ligas. Mas, remate a remate, foi exatamente da média. O que o torna insubstituível é outra coisa, e é isso que o Porto tem de procurar lá fora."

**0:30 · As prioridades do Farioli** → gráfico `farioli_prioridades.png`. Explica cada bloco e a citação "preferimos vê-lo a usar os pés".

**2:30 · Fase 1: o funil** → `farioli_fase1.png`. Mostra os 113 guarda-redes, a estrela do Diogo Costa (à direita, mas não no topo), e quem é eliminado e porquê (preço, idade, clube).

**4:30 · Fase 2: o ranking** → `farioli_ranking.png`. As barras estão divididas por bloco, por isso vê-se *onde* cada um ganha ou perde.

**6:00 · Os 3 finalistas** (Nübel, Murić e um jovem). Para cada um: um cartão, 2 lances com os pés, 1 defesa e 1 erro.

**10:00 · Recomendação + "mudem os pesos"**: "se o Farioli valorizasse ainda mais a defesa, o Carnesecchi subia ao 1.º lugar".

---

## 6. Limitações (diz pelo menos as duas primeiras no vídeo)
1. **O estilo vem de 7–13 jogos** (2026/27). A FotMob só mostra a época atual na página do jogador, e uma amostra destas pode mudar muito.
2. **As ligas não estão ajustadas pela força:** 80% de defesas na Liga Portugal não é igual a 80% na Premier League.
3. **Faltam ligas:** Ligue 1, Eredivisie, Bélgica e Brasil. Não consegui o ranking FotMob de 2025/26 para estas ligas. Podes adicioná-las a `fotmob_defesa_remates_2025_26.csv` à mão, com as mesmas colunas.
4. Em 2025/26, os minutos foram estimados a partir de defesas ÷ defesas por 90 (erro de ±1–2%).
5. Os valores de mercado são os da FotMob e o clube atual é o de hoje. Confirma no Transfermarkt.
6. "Ações de líbero" e "saídas a cruzamentos" são definições da FotMob e não captam o **posicionamento**, que tem de ser visto em vídeo.

## Fontes
- Citação do Farioli sobre o uso dos pés: [Bola na Rede](https://bolanarede.pt/especial-bola-na-rede/atualidade/francesco-farioli-rendido-a-diogo-costa-e-o-que-da-ter-um-dos-melhores-guarda-redes-do-mundo/) / [A Bola](https://www.abola.pt/noticias/farioli-destaca-aura-de-diogo-costa-e-deixa-reparo-relvado-nao-estava-em-boas-condicoes-2025122221134529466) `[CONFIRMAR a frase exata]`
- FotMob, rankings 2025/26: [Premier League](https://www.fotmob.com/leagues/47/stats/season/27110/players/_goals_prevented/premier-league) · [La Liga](https://www.fotmob.com/leagues/87/stats/season/27233/players/_goals_prevented/laliga) · [Serie A](https://www.fotmob.com/leagues/55/stats/season/27044/players/_goals_prevented/serie) · [Bundesliga](https://www.fotmob.com/leagues/54/stats/season/26891/players/_goals_prevented/bundesliga-players) · [Championship](https://www.fotmob.com/leagues/48/stats/season/27195/players/_goals_prevented/championship) · [Liga Portugal](https://www.fotmob.com/leagues/61/stats/season/27181/players/_goals_prevented/liga-portugal)
