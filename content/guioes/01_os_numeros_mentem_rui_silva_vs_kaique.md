# Os números mentem? Rui Silva vs Kaique: quem deve ser o n.º 1 do Sporting?

**Formato:** "Os números mentem?" · **Duração alvo:** 7–9 min (+ 2 Shorts)
**Dados:** FotMob, Liga Portugal **2025/26** (época completa, os dois titulares toda a época), recolhidos a 2026-11-02 → `content/dados/fotmob_liga_portugal_2025_26.csv`

## A história que os dados contam

| | Rui Silva (Sporting) | Kaique (Nacional) |
|---|---|---|
| Minutos | 2880 | ~2526 (estimado) |
| **Defesas %** | **76,8%** (3.º da Liga) | 71,3% (6.º) |
| **Golos evitados /90** (xGOT − golos) | +0,11 | **+0,17** |
| Golos evitados (total) | +3,5 | **+4,9** (3.º da Liga) |
| Remates enquadrados sofridos /90 | 3,09 | **4,35** |
| Golos sofridos /90 | 0,72 | 1,25 |

**A tese do vídeo:** a métrica clássica (defesas %) diz Rui Silva. A métrica moderna (golos evitados) diz Kaique.
→ **As duas estão "certas"**, mas medem coisas diferentes. Explicar esta diferença é o que te mostra como analista.

### Porque é que as duas métricas discordam (o centro do vídeo)
- **Defesas %** = defesas ÷ remates enquadrados. Trata todos os remates como iguais: um remate fraco ao centro conta o mesmo que um remate ao ângulo.
- **Golos evitados** = golos esperados pela **qualidade de cada remate enquadrado** (xGOT: colocação, velocidade, distância) − golos sofridos. Positivo quer dizer que sofreu menos do que um guarda-redes médio sofreria.
- O Kaique, no Nacional, enfrentou **40% mais remates enquadrados por jogo** e, provavelmente, remates mais difíceis. A percentagem dele cai, mas ele evitou mais golos do que o esperado.
- O Rui Silva, num Sporting dominante, enfrenta poucos remates. É muito eficaz neles, mas tem menos oportunidades de "fazer a diferença".

> Atenção: a época 2026/27 ainda tem **amostras minúsculas** (o Kaique tem 180 min no campeonato). **Não as uses para conclusões**, só como nota.

---

## Gráficos (já gerados em `content/graficos/`)
- `comparar_rui_silva_kaique_pereira_2025_26.png` (+ `_vertical`, para o Short)
- `percentis_rui_silva_2025_26.png` e `percentis_kaique_pereira_2025_26.png`

Para regenerar ou atualizar:
```bash
python content/analise.py comparar --csv content/dados/fotmob_liga_portugal_2025_26.csv \
  --jogadores "Rui Silva" "Kaique Pereira" --titulo "Rui Silva vs Kaique · 2025/26"
python content/analise.py percentis --csv content/dados/fotmob_liga_portugal_2025_26.csv --jogador "Kaique Pereira"
```

---

## Guião

### 0:00–0:20 · GANCHO
**Ecrã:** o gráfico com só a linha "Defesas %" visível.
> "Se olharmos para a estatística que toda a gente usa, o Rui Silva foi melhor do que o Kaique na época passada: 77% de defesas contra 71%. Então porque é que o Sporting pôs o Kaique na baliza? [revela a linha dos golos evitados] Porque há outra métrica que diz exatamente o contrário."

### 0:20–1:00 · CONTEXTO
**Ecrã:** dois cartões de jogador.
- **Rui Silva:** 32 anos, campeão em 2024/25, titular do Sporting em toda a época 2025/26, contrato até 2028 `[CONFIRMAR]`.
- **Kaique:** 23 anos, contratado ao Palmeiras em agosto (cláusula de 80 M€, segundo o Sporting), titular do Nacional emprestado em 2025/26. Ganhou o lugar em outubro e estreou-se na Champions em Lens (2-0) `[CONFIRMAR]`.

### 1:00–3:30 · DUAS MÉTRICAS, DUAS RESPOSTAS
1. **Defesas %:** "O Rui Silva foi o 3.º melhor da Liga. O Kaique foi o 6.º."
2. **Volume:** "Mas o Kaique enfrentou 4,35 remates enquadrados por jogo. O Rui Silva enfrentou 3,09."
3. **O que é o xGOT** (30 s, com desenho): a baliza dividida em zonas. "Um remate aqui [canto superior] vale quase um golo. Aqui [ao centro, rasteiro] vale muito pouco."
4. **Golos evitados:** "O Kaique evitou 4,9 golos a mais do que o esperado, o 3.º melhor valor da Liga. O Rui Silva evitou 3,5. Por cada 90 minutos: +0,17 contra +0,11."
5. **Conclusão desta parte:** "O Rui Silva é muito fiável nos remates que lhe chegam. O Kaique fez mais com remates mais difíceis."

### 3:30–6:00 · O VÍDEO CONFIRMA?
3–4 lances congelados e desenhados:
- **Kaique:** uma defesa difícil no Nacional (remate colocado, que mostra o xGOT alto)
- **Kaique:** um lance com os pés (o Sporting constrói desde trás e ele vem de uma equipa que defende baixo, por isso é uma dúvida legítima)
- **Rui Silva:** um lance de leitura e posicionamento (o tipo de "defesa fácil" que é fácil porque ele estava bem posicionado, e que nenhuma métrica capta)
- **Um golo sofrido** de cada um, analisado sem crucificar ninguém

### 6:00–6:45 · LIMITES DOS NÚMEROS (dá credibilidade)
- O xGOT **não mede posicionamento**: um guarda-redes bem colocado faz remates parecerem fáceis.
- Os golos evitados oscilam bastante de época para época, por isso uma época sozinha não chega.
- Os números de 2026/27 ainda são poucos jogos.

### 6:45–7:45 · VEREDICTO
| | Rui Silva | Kaique |
|---|---|---|
| Os dados dizem | Muito eficaz, fiável | Evita mais golos em remates difíceis |
| O vídeo diz | [PREENCHER] | [PREENCHER] |
| Perfil | Presente, experiência | Futuro, valor de mercado |

> "Os números não mentem, mas respondem à pergunta que lhes fazes. Se perguntares 'quem defende mais remates', é o Rui Silva. Se perguntares 'quem evita mais golos do que o esperado', é o Kaique. E vocês, quem punham na baliza?"

---

## Shorts
1. **"A estatística que engana sobre guarda-redes"** (45 s): defesas % vs golos evitados com este exemplo.
2. **"Kaique em números"** (30 s): gráfico de percentis vertical.

## Fontes
- Dados: FotMob, rankings da Liga Portugal 2025/26 (golos evitados, defesas %, defesas/90)
- Contexto: [Sporting: Kaique Pereira joins Sporting CP](https://www.sporting.pt/en/news/football/main-team/2026-08-29/kaique-pereira-joins-sporting-cp) · [A Bola: Kaique ganha lugar](https://www.abola.pt/noticias/kaique-ganha-lugar-mas-rui-silva-vai-a-luta-no-sporting-2026101611314676265) · [A Bola: estreia em Lens](https://www.abola.pt/noticias/o-kaique-e-um-monstro-2026101917222960036)
