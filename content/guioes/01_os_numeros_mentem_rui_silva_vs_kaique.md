# Os números mentem? Rui Silva vs Kaique: quem deve ser o n.º 1 do Sporting?

**Formato:** "Os números mentem?" · **Duração alvo:** 7–9 min (+ 2 Shorts)
**Tese do vídeo:** O Rui Borges trocou o campeão Rui Silva pelo Kaique, de 23 anos. Os dados justificam a troca ou é uma aposta no futuro?

> ⚠️ **Antes de gravar:** todos os campos `[PREENCHER]` vêm dos dados que vais recolher (passo 1).
> **Nunca inventes um número.** Se não encontrares uma métrica para os dois, não a uses. O script de gráficos já ignora métricas incompletas.
> Os factos de contexto marcados com `[CONFIRMAR]` vêm da imprensa (A Bola, Record) e convém verificá-los antes de publicar.

---

## Passo 1: Recolha de dados (30–45 min)

Preenche `content/dados/liga_portugal_manual.csv` à mão (não uses scraping, porque os termos destes sites proíbem-no):

| Coluna | Onde encontrar |
|---|---|
| jogos, minutos, golos_sofridos, jogos_sem_sofrer | FotMob → jogador → época → Liga Portugal |
| defesas, remates_enquadrados_contra | Sofascore → "Defesas" (enquadrados = defesas + golos sofridos, excluindo autogolos) |
| xgot_contra | FotMob mostra "Golos evitados" (= xGOT contra − golos). Se só tiveres os golos evitados, calcula xgot_contra = golos_sofridos + golos_evitados |
| penaltis_enfrentados / defendidos | FotMob / Sofascore |
| passes_tentados / certos, passes_longos | Sofascore → "Distribuição" |
| saidas_cruzamento, acoes_fora_area | Sofascore ("Saídas altas", "Ações como líbero"), se existirem |

Recolhe **duas épocas**:
- **2025/26:** Rui Silva no Sporting, Kaique no Nacional (época completa, com amostra grande)
- **2026/27:** os dois no Sporting (amostra ainda curta, que deves mencionar no vídeo)

Também tens dados reais no teu projeto: **o Rui Silva no Betis, La Liga 2024/25** (FBref): 15 jogos, **67,3% de defesas**, perto da mediana da liga (65,6%), cerca do **percentil 55** entre 33 guarda-redes com ≥450 min. Isto dá contexto: era um guarda-redes "dentro da média" em La Liga, com uma amostra curta.

## Passo 2: Gerar os gráficos

```bash
# Época completa 2025/26
python content/graficos.py comparar --csv content/dados/liga_portugal_manual.csv \
  --epoca 2025/26 --jogadores "Rui Silva" "Kaique" \
  --titulo "Rui Silva vs Kaique · 2025/26"

# Esta época (amostra curta!)
python content/graficos.py comparar --csv content/dados/liga_portugal_manual.csv \
  --epoca 2026/27 --jogadores "Rui Silva" "Kaique" \
  --titulo "Rui Silva vs Kaique · 2026/27 (até agora)"

# Versões verticais para os Shorts
python content/graficos.py comparar ... --vertical
```

---

## Guião

### 0:00–0:20 · GANCHO
**Ecrã:** Kaique na baliza vs Lens (imagem congelada) → corte rápido para o Rui Silva a festejar o título de 2024/25.

> "Há três meses, o Rui Silva era o titular indiscutível do Sporting, e já tinha sido campeão. Hoje está no banco. Quem o tirou de lá foi um miúdo de 23 anos que, na época passada, jogava no Nacional. Foi uma boa decisão? Vamos ver o que dizem os números, e onde é que os números **não chegam**."

### 0:20–1:15 · CONTEXTO
**Ecrã:** dois "cartões de jogador" lado a lado (Canva): foto, idade, clube anterior, contrato.

- **Rui Silva:** 32 anos, chegou do Betis em janeiro de 2025, campeão em 2024/25, contrato até 2028 `[CONFIRMAR]`.
- **Kaique:** 23 anos, contratado ao Palmeiras por ~4 M€ `[CONFIRMAR]`, emprestado ao Nacional na época passada (e antes ao Farense). Segundo a imprensa, foi o guarda-redes com mais penáltis defendidos da Liga (4) `[CONFIRMAR]`.
- Ganhou a titularidade em outubro, com a estreia na Champions em Lens (vitória por 2-0) `[CONFIRMAR]`.

> "Primeiro aviso: estamos a comparar um guarda-redes de uma equipa que domina com um guarda-redes de uma equipa que passa o jogo a defender. Isso muda tudo nos números, e já vão ver porquê."

### 1:15–3:30 · OS DADOS DA ÉPOCA PASSADA (2025/26)
**Ecrã:** gráfico `comparar_rui_silva_kaique_2025_26.png`. Revela uma métrica de cada vez (no CapCut: corta a imagem por camadas ou usa um retângulo escuro por cima que vais tirando).

Ordem de narração (só um ponto por métrica):
1. **Defesas %**: "O Kaique defendeu [PREENCHER]% dos remates enquadrados, contra [PREENCHER]% do Rui Silva."
2. **Volume**: "Mas o Kaique enfrentou [PREENCHER] remates enquadrados, e o Rui Silva só [PREENCHER]. No Nacional, ele foi muito mais testado."
   → **Ponto de analista:** um guarda-redes de uma equipa grande enfrenta poucos remates, e muitas vezes remates de alta qualidade (contra-ataques, 1x1). Por isso, a defesa% sozinha engana.
3. **Golos evitados (xGOT − golos)**: "É por isso que esta métrica é mais justa: mede se o guarda-redes sofreu mais ou menos do que o esperado pela **qualidade** dos remates. Aqui, [PREENCHER: quem está acima de zero]."
4. **Penáltis**: o dado curioso, mas uma **amostra minúscula**. Diz isso mesmo.
5. **Passes**: "O Sporting constrói desde trás. [PREENCHER: quem é mais seguro com os pés]."

> Se os dados contradisserem a narrativa (por exemplo, se o Rui Silva tiver melhores golos evitados), **esse é o vídeo**. Não escondas: "Os números não explicam esta troca. Então o que é que o treinador viu?"

### 3:30–6:00 · O VÍDEO CONFIRMA OU DESMENTE?
**Ecrã:** 3–4 lances curtos (5–8 s cada), sempre **congelados e desenhados** (ver aviso de direitos no fim).

Escolhe:
- **1 lance do Kaique que confirma o ponto forte** (ex.: defesa a remate de perto, reflexos, penálti)
- **1 lance do Kaique com o pé** (saída de pressão ou passe vertical)
- **1 lance do Rui Silva que mostra o seu valor** (posicionamento, leitura, comunicação)
- **1 lance de dúvida** (um golo sofrido por um deles, analisado sem crucificar ninguém)

Para cada lance, segue o mesmo esquema de narração:
> "Pausa aqui. Olhem para os apoios [círculo nos pés]. Ele está [equilibrado/atrasado]. A bola vai [aqui, seta]. Por isso é que [conclusão]."

O que procurar num guarda-redes, para teres vocabulário:
- **Posição inicial:** está no ângulo da bola? Ajustou-se antes do remate?
- **Apoios:** está parado e equilibrado no momento do remate (*set position*)?
- **Tomada de decisão em cruzamentos:** sai, fica ou "sai a meio"?
- **Profundidade:** qual a distância à linha de golo quando a equipa ataca? (o líbero)
- **Distribuição:** escolhe a opção segura ou a progressiva? Sob pressão, como reage?

### 6:00–7:00 · ESTA ÉPOCA (amostra curta)
**Ecrã:** gráfico 2026/27.

> "Com [PREENCHER] jogos, ainda é cedo para tirar conclusões. Uma ou duas defesas mudam tudo. Mas a tendência é [PREENCHER]."

### 7:00–8:00 · VEREDICTO EM FORMATO DE RELATÓRIO
**Ecrã:** cartão final com duas colunas.

| | Rui Silva | Kaique |
|---|---|---|
| Ponto forte (dados) | [PREENCHER] | [PREENCHER] |
| Ponto forte (vídeo) | [PREENCHER] | [PREENCHER] |
| A melhorar | [PREENCHER] | [PREENCHER] |
| Perfil | Experiência, fiabilidade | Potencial, valor de mercado |

> "A minha leitura: [opinião, assumida como tua]. Os números dizem X. O vídeo diz Y. A decisão do treinador provavelmente também tem a ver com [idade, valor de revenda, projeto]. E vocês, quem punham na baliza?"

### 8:00 · FECHO
> "O gráfico completo e o relatório estão no link da descrição. No próximo vídeo: se o Diogo Costa sair do Porto, quem deve substituí-lo?"

---

## Shorts que saem deste vídeo
1. **"Os números do Kaique no Nacional"** (30 s): só o gráfico vertical + um lance.
2. **"Porque é que a defesa% engana"** (45 s): explica o efeito de volume com este caso. É um conteúdo educativo que se partilha muito.

## Título e miniatura
- Títulos possíveis: *"Rui Silva ou Kaique? Os números não dizem o que pensas"* / *"O Sporting acertou na baliza?"*
- Miniatura: as duas caras (recortadas) + um "?" grande + um número-chave do gráfico.

## ⚠️ Direitos de imagem
Usa clips muito curtos, sempre com comentário e desenho por cima, ou imagens congeladas. Nunca uses mais de alguns segundos seguidos de transmissão.

## Fontes de contexto (verificar)
- A Bola: [Kaique reforça a baliza do Sporting](https://www.abola.pt/noticias/mercado-oficial-kaique-reforca-a-baliza-do-sporting-2026082718302315492)
- A Bola: [Kaique ganha lugar, mas Rui Silva vai à luta](https://www.abola.pt/noticias/kaique-ganha-lugar-mas-rui-silva-vai-a-luta-no-sporting-2026101611314676265)
- A Bola: [Kaique estreou-se na vitória em Lens](https://www.abola.pt/noticias/o-kaique-e-um-monstro-2026101917222960036)
- A Bola: [Rui Silva brilha mas Kaique volta à baliza](https://www.abola.pt/noticias/sporting-rui-silva-brilha-mas-kaique-volta-a-baliza-2026102822295343867)
