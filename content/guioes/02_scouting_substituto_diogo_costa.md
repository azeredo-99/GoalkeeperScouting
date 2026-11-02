# Scouting: se o Diogo Costa sair, quem deve o FC Porto contratar?

**Formato:** "Scouting: substituto para o clube X" · **Duração alvo:** 8–10 min (+ 2 Shorts)
**Porque é o melhor vídeo para portfólio:** é *exatamente* o trabalho de um departamento de scouting. Defines o perfil, filtras com dados, validas com vídeo e apresentas uma shortlist com recomendação.

> ⚠️ Os factos marcados `[CONFIRMAR]` (cláusula, idades atuais, clubes atuais) têm de ser verificados no Transfermarkt antes de publicar.
> Os dados de 2024/25 do teu projeto **servem para mostrar o método**. Alguns desses guarda-redes já mudaram de clube desde então. É precisamente isso que deves verificar no passo 3.

---

## Passo 1: Definir o perfil (o que é que o Porto perde?)

Gera os gráficos com os **dados reais StatsBomb** do teu projeto:

```bash
python content/graficos.py percentis --jogador "Diogo Meireles Costa" \
  --competicao 55 --epoca-id 282 --titulo "Diogo Costa · Euro 2024"

python content/graficos.py percentis --jogador "Diogo Meireles Costa" \
  --competicao 43 --epoca-id 106 --titulo "Diogo Costa · Mundial 2022"
```

O que os dados mostram (já calculado, Euro 2024, 21 guarda-redes com ≥270 min):

| Métrica | Valor | Percentil | Leitura |
|---|---|---|---|
| Defesas % | 84,6% | **83** | Muito acima da média |
| Passes certos % | 90,3% | **98** | O mais seguro do torneio com os pés |
| Comprimento médio do passe | 28,9 m | 7 | Joga **curto** |
| Bolas longas % | 19,5% | 2 | Quase nunca "chuta para a frente" |
| Ações de líbero /90 | 1,06 | 40 | Médio |
| Distância dessas ações | 17,3 m | 60 | Médio |

**Comparação com o Mundial 2022** (mesmo guarda-redes, outro selecionador): 69,8% de passes certos e 37,7% de bolas longas. No Euro 2024 jogou muito mais curto.
→ **Ponto de analista:** o perfil de distribuição depende muito do **modelo de jogo do treinador**. Isto é uma hipótese a validar em vídeo, não uma certeza. Mas é exatamente o tipo de nuance que um recrutador quer ver.

⚠️ Amostra curta: 5 a 6 jogos por torneio. Diz isso no vídeo. A seguir, valida com os dados de clube (2025/26) que recolheres à mão.

**Perfil-alvo resultante:**
1. **Guarda-redes de construção:** seguro com os pés sob pressão, confortável a jogar curto
2. **Shot-stopper acima da média:** defesa% e golos evitados acima da mediana da liga
3. **Idade ≤ 26:** para ter valor de revenda (o modelo de negócio do Porto)
4. **Custo realista:** nunca perto dos valores de uma venda do Diogo Costa `[CONFIRMAR cláusula]`
5. **Bónus:** experiência de penáltis e de jogos grandes (o Diogo Costa defendeu 3 penáltis no desempate contra a Eslovénia no Euro 2024)

## Passo 2: Filtro com dados

```bash
python content/graficos.py shortlist --nascido-depois 2000 --min-minutos 1800
```

Isto gera o gráfico **defesas % × remates enquadrados sofridos/90** nas 5 grandes ligas em 2024/25, com os guarda-redes nascidos em 2000 ou depois destacados.

- **Quadrante superior direito** (muito testados e com muitas defesas): os mais interessantes para o perfil 2
- **Quadrante inferior direito:** boa eficácia, mas com pouco volume (pede mais validação)

Em 2024/25, os jovens que se destacam no quadrante direito são Carnesecchi, Joan García, Fofana, Chevalier e Atubolu.
**Mas** pelo menos alguns já foram para clubes fora do alcance do Porto `[CONFIRMAR no Transfermarkt]`. Não escondas isto. Usa-o no vídeo:

> "Este é o problema real do scouting: quando um guarda-redes aparece nos números de todos, já é tarde e caro demais. O trabalho é encontrar o próximo **antes** disso."

Por isso, alarga o filtro com dados de 2025/26 recolhidos à mão (FotMob/Sofascore) em `content/dados/substitutos_diogo_costa.csv`, olhando para:
- **Liga Portugal** (guarda-redes de clubes médios, mais baratos e já adaptados)
- **Ligas de "trampolim":** Bélgica, Países Baixos, Áustria, Suíça, Escandinávia, Brasil
- **Segundas ligas das 5 grandes**

## Passo 3: Validação (o que separa um analista de uma folha de Excel)

Para cada um dos 3 finalistas, verifica:
- **Transfermarkt:** clube atual, contrato, valor, lesões
- **Vídeo:** 3 jogos completos ou resumos (procura a distribuição sob pressão, porque é o ponto 1 do perfil)
- **Contexto:** a equipa dele constrói curto? Se joga num clube de bola longa, a percentagem de passes certos vai parecer baixa sem ser culpa dele

---

## Guião

### 0:00–0:20 · GANCHO
> "O Diogo Costa é provavelmente o ativo mais valioso do FC Porto. Um dia vai sair. Se fosse eu o responsável pelo scouting, quem é que ia buscar para o lugar dele? Vou fazer o processo completo, como se faz num clube."

### 0:20–2:30 · O QUE O PORTO PERDE
**Ecrã:** gráfico de percentis do Euro 2024.
- Revela as barras uma a uma. A grande mensagem é **percentil 98 em passes certos** e **percentil 2 em bolas longas**: um guarda-redes de construção.
- Mostra 1 a 2 lances de saída curta sob pressão (congelados, com setas para as linhas de passe).
- Faz a comparação com o Mundial 2022: "o estilo dele mudou com o selecionador".
- Fecha com o cartão do **perfil-alvo** (os 5 pontos acima).

### 2:30–4:30 · O FILTRO
**Ecrã:** gráfico `shortlist_2000.png`.
> "Peguei em todos os guarda-redes das 5 grandes ligas com mais de 1800 minutos e destaquei os nascidos em 2000 ou depois. Eixo horizontal: percentagem de defesas. Eixo vertical: quantos remates enquadrados sofrem por jogo."
- Explica os quadrantes.
- Dá a revelação: "os melhores já foram vendidos" → passa para a pesquisa alargada (os dados de 2025/26).

### 4:30–8:00 · A SHORTLIST (3 nomes)
Para cada candidato (cerca de 1 min cada), um **cartão fixo** (Canva):

```
NOME · idade · clube · contrato · valor de mercado [Transfermarkt]
DADOS:   defesas % [pct] · golos evitados [pct] · passes certos % [pct]
VÍDEO:   1 lance forte + 1 lance de dúvida
ENCAIXE NO PERFIL: ✅ construção  ✅ defesas  ⚠️ cruzamentos
RISCO:   [adaptação / preço / lesões]
```

Ordena do "mais seguro" ao "mais aposta".

### 8:00–9:00 · RECOMENDAÇÃO
> "Se eu tivesse de escolher um, escolhia [NOME], porque [razão ligada ao perfil, não ao nome]. Plano B: [NOME]. E vocês?"

### 9:00 · FECHO
> "O relatório em PDF de cada candidato está na descrição. Se gostaram deste formato, digam-me qual é o próximo clube."

---

## Shorts que saem deste vídeo
1. **"O Diogo Costa em 30 segundos de dados"**: o gráfico de percentis vertical (`--vertical`).
2. **"Quando um guarda-redes aparece nos dados, já é tarde"**: o gráfico de dispersão com os nomes que foram vendidos.

## Extra para portfólio (muito valorizado)
Transforma este vídeo num **relatório de 2 páginas** (o teu app gera o Scouting Report de cada guarda-redes) e publica-o no LinkedIn com o título *"Relatório de scouting: substituto para o Diogo Costa"*. É exatamente o documento que um diretor desportivo lê.
