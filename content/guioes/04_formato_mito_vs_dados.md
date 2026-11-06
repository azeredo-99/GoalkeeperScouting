# Formato "Mito vs Dados" (inspirado no @thefinalthird.pro)

Esta é a análise do reel *"Messi fans say Ronaldo statpads…"* (155 mil gostos numa conta com 8 publicações), feita a partir de 7 capturas de ecrã, e a sua adaptação aos teus temas.

## 1. Estrutura do reel (cena a cena)

| # | Cena | Título fixo (topo) | Legenda (voz) | O que se vê |
|---|---|---|---|---|
| 1 | **Gancho: o mito, dos dois lados** | "Messi fans: **Ronaldo stat-pads**" → "Ronaldo fans: **Messi stat-pads**" | "Ronaldo **stat-pads.**" | Messi e Ronaldo frente a frente no meio-campo, com os adeptos de cada um em grupo ao lado, etiquetas de nome e um foco de luz no chão |
| 2 | **Marca da série** | (sem título) | "of Myth vs **Data.**" | "ANOTHER EPISODE · **MYTH** vs **DATA** · WHO STAT-PADS?" no círculo central |
| 3 | **Credibilidade** | "**1,921** goals checked" | "to see whose goals…" | Número gigante a dourado: "1,921 GOALS CHECKED" |
| 4 | **O básico** | "First, **the basics**" | "Ronaldo: **985** in **1343.**" | 2 cartões escuros: MESSI 936 golos / 1,183 jogos · RONALDO 985 / (contador a subir) |
| 5 | **A pergunta** | "**Match-winning** goals" | "**Match-winning** goals?" | Messi (camisola 10) sozinho, câmara por trás |
| 6 | **O número absoluto** | "**Match-winning** goals" | "Ronaldo has **243.**" | Ronaldo a festejar, "243 · RONALDO · MATCH-WINNING GOALS" |
| 7 | **O número relativo (a grande ideia)** | "Goals that **won the game**" | "and **24.7%** of…" | 2 cartões com 100 bolinhas cada: 20,8% (rosa) vs 24,7% (dourado) |

**A lição analítica do vídeo:** começa pelos totais (985 golos, 243 golos decisivos) e depois **normaliza** (24,7% dos golos). Passar de totais para taxas é o que separa a opinião da análise, e é exatamente o que fizeste com o Rui Silva e o Kaique (golos evitados por 90).

## 2. Sistema visual (para copiar o "aspeto")

- **Formato:** 9:16, 1080×1920. O conteúdo fica dentro de uma zona segura (há margem preta em cima e em baixo para a interface do Instagram)
- **Camadas, sempre na mesma posição:**
  1. Logótipo pequeno no canto superior esquerdo (círculo + nome em letra monoespaçada)
  2. **Título da secção** grande, alinhado à esquerda, branco com 1 ou 2 palavras a **dourado**
  3. **Legenda da voz** ao centro, numa "pílula" escura semitransparente, com a palavra-chave a dourado
  4. Cena 3D ou cartões de dados na metade de baixo
- **Cores:** fundo preto ou verde-escuro; dourado (~#E6C35C) como cor de destaque; uma cor por jogador (Messi rosa ~#F0569B, Ronaldo dourado); azul (~#3B82F6) só para "DATA"
- **Letras:** títulos em sans-serif bold (Inter, grátis no Google Fonts); etiquetas e unidades em **monoespaçada maiúscula com muito espaçamento** ("GOALS CHECKED", "MESSI"), por exemplo JetBrains Mono ou Space Mono (ambas grátis)
- **Números grandes** com um brilho suave à volta (glow); os contadores sobem de 0 até ao valor
- **Cartões:** retângulos escuros, cantos arredondados, borda fina, etiqueta monoespaçada no topo
- **Gráfico de bolinhas (waffle):** 10×10 = 100%. A última bolinha preenche-se parcialmente (20,8% = 20 cheias + 0,8 de uma)
- **3D:** bonecos simples (cápsulas, cabeça esférica sem cara), bancada feita de "pixels" coloridos aleatórios, desfoque de fundo e brilho no relvado

## 3. Como se faz (estimativa: não sei qual é a ferramenta exata deles)

O aspeto (3D simples, bancada de pixels, interface muito precisa com letra monoespaçada) sugere **vídeo gerado por código**:
- **Remotion** (vídeo em React; grátis para uso individual) + **React Three Fiber / Three.js** (3D no browser, grátis e open source)
- Cada cena é um componente; as legendas são sincronizadas com a voz. Muitos criadores usam IA para escrever este código

| Caminho | Ferramentas (grátis) | Dificuldade | Fica parecido? |
|---|---|---|---|
| **A. Código (recomendado para ti)** | Node.js + Remotion + Three.js; voz gravada por ti; legendas no Remotion ou no CapCut | Média: é programação, e eu consigo escrevê-la contigo | ✅ Muito |
| B. Blender + CapCut | Blender (cenas 3D) + Mixamo (animações) + CapCut (texto, legendas, cartões) | Alta (3–4 semanas a aprender Blender) | ✅ Muito |
| C. 2D primeiro | Python/matplotlib (o teu `analise.py`) ou Canva + CapCut, sem bonecos 3D | Baixa | 🟡 O layout e a narrativa sim; o 3D não |

## 4. Adaptação: "Mito vs Dados", episódio 1: Kaique vs Rui Silva

Dados: FotMob, Liga Portugal 2025/26 (ver `01_os_numeros_mentem_rui_silva_vs_kaique.md`).

| # | Título fixo | Legenda / voz | Visual |
|---|---|---|---|
| 1 | "Uns: **o Kaique é melhor**" → "Outros: **o Rui Silva defende mais**" | "O Rui Silva **defende mais.**" | Os dois guarda-redes frente a frente na pequena área, etiquetas RUI SILVA / KAIQUE |
| 2 | — | "Mais um episódio de Mito vs **Dados.**" | "MAIS UM EPISÓDIO · **MITO** vs **DADOS** · QUEM É O N.º 1?" |
| 3 | "**221** remates analisados" | "para ver quem defende melhor" | "221 · REMATES ENQUADRADOS" (99 do Rui Silva + 122 do Kaique) |
| 4 | "Primeiro, **o básico**" | "Kaique: **87** defesas em **122.**" | Cartões: RUI SILVA 76 defesas / 99 remates · KAIQUE 87 / 122 |
| 5 | "**Defesas %**" | "Quem defende **mais**?" | Waffle: 76,8% vs 71,3%. "O mito parece confirmado…" |
| 6 | "Mas **que remates?**" | "Nem todos os remates são **iguais.**" | Baliza dividida em zonas (xGOT): o canto vale quase um golo, o centro vale pouco |
| 7 | "Golos **evitados**" | "O Kaique evitou **4,9.**" | Contador +3,5 vs **+4,9** |
| 8 | "Por **90 minutos**" | "**+0,17** contra **+0,11.**" | Cartões por 90 (normalizar, como no vídeo deles) |
| 9 | "**Veredicto**" | "Os dois lados têm razão. Só um olha para a métrica **certa.**" | "MITO: o Rui Silva defende mais ✔ · DADOS: o Kaique evita mais golos ✔" |

Outros episódios da série:
- "O Diogo Costa é o melhor guarda-redes da Liga?" (80% de defesas, percentil 99, mas golos evitados no percentil 49)
- "O Porto precisa de um guarda-redes que defenda ou que jogue com os pés?" (o modelo do Farioli)

## 5. O resto do reel (mais 10 capturas)

| Cena | O que fazem | Técnica a reter |
|---|---|---|
| "Won by one goal" | Cada golo decisivo aparece como uma pequena peça com o resultado (1-0, 2-1, 3-2); contador 111 vs 142 | **Ver cada ponto de dados**: a amostra torna-se concreta |
| "Take their goals away" | O guarda-redes sozinho na baliza: "e se tirássemos os golos?" | **Contrafactual**: o que acontecia sem o jogador |
| "Bicycle vs Juventus: gone" / "Ankara Messi: never happened" / "'Ronaldo Jr': nope" | Golos famosos recriados em 3D e "apagados", com efeito VHS, "◀◀ REWIND", o texto "GONE." e a etiqueta do jogo ("JUVENTUS 0-3 REAL MADRID · UCL 2018") | **Momentos icónicos + humor** ("OUCH") fazem as pessoas reconhecer e partilhar |
| "Points lost without them" | Barras com a parte perdida a vermelho: −362 vs −370 | Barra **subtrativa** |
| "Points per goal" | Moedas grandes: 0,39 vs 0,42 | Segunda **normalização** |
| "Already 4 up" | Marcador "BARÇA 7-0 · ALREADY 4 UP" e a fila de resultados dos fins de semana | **Estado do jogo**: golos com o jogo já ganho ("stat-padding") |
| "Case closed." | Celebração do vencedor, texto gigante esbatido por trás, luz dourada | **Final com assinatura** |

**Arco completo:** discussão → série → amostra → básico → métrica 1 → normalizar → métrica 2 → contrafactual (com momentos icónicos) → normalizar outra vez → contexto do jogo → veredicto.

### O que já passou para o episódio 01
- **Contrafactual**, cena 08 "E se…?": "troca-os por um guarda-redes médio". Barra = golos esperados contra (sofridos + evitados), com a parte evitada às riscas menta. Rui Silva 23 sofridos, +3,5 evitados; Kaique 35, +4,9.
- **Efeito rebobinar** próprio ("◀◀ E SE…?", linhas de vídeo e separação de cor) e **etiqueta de contexto** (equipa · época).

### Para episódios seguintes (precisam de dados jogo a jogo)
- **Peça por defesa**, com o minuto e o resultado no momento (por exemplo "67' · 1-0")
- **Estado do jogo:** defesas com o jogo empatado ou a perder, contra defesas com o jogo resolvido (o equivalente do "already 4 up")
- **Defesas icónicas recriadas**, cada uma com a etiqueta do jogo
- Fonte possível: a página de cada jogo na FotMob (o mapa de remates), recolhida à mão
