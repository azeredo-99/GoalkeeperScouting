# Vídeos verticais (Remotion)

Vídeos 9:16 (1080×1920, 30 fps) de análise de guarda-redes, gerados por código.
O formato (título de secção, legenda da voz palavra a palavra, cartões, contadores, grelhas) foi inspirado nos reels de dados de futebol. A identidade é própria: nome, cores, letras, grelha em forma de rede de baliza e barra de capítulos.

## Começar (no teu computador)

1. Instala o **Node.js** (versão LTS) em nodejs.org
2. Nesta pasta:
   ```bash
   npm install
   npm run studio      # abre o editor no browser, com pré-visualização em tempo real
   npm run render      # gera out/ep01.mp4
   ```
   Na primeira vez, o Remotion descarrega sozinho o browser que usa para o render.

## Onde mudar o quê

| Ficheiro | O quê |
|---|---|
| `src/marca.ts` | **Nome da série** (provisório: "ENTRE OS POSTES"), a tua conta, cores e letras |
| `src/episodios/ep01.tsx` | O episódio: cenas, títulos, legendas, dados e duração de cada cena |
| `src/scenes/cenas.tsx` | Tipos de cena: frente a frente, abertura, número grande, cartões, grelhas, zonas da baliza, veredicto |
| `src/components/` | Peças reutilizáveis: moldura, legenda, contador, cartão, grelha, relvado, guarda-redes, baliza |

Nos títulos e legendas, `*palavra*` fica em destaque.

## Novo episódio
Copia `src/episodios/ep01.tsx` para `ep02.tsx`, muda os dados e as frases, e regista-o em `src/Root.tsx` (igual ao `Ep01`).

## Voz
1. Grava a voz a ler as legendas (telemóvel, num sítio sem eco) e guarda-a em `public/voz-ep01.mp3`
2. Em `src/Root.tsx`, dentro do `Video`, acrescenta `<Audio src={staticFile("voz-ep01.mp3")} />` (importado de `remotion`)
3. Acerta os `segundos` de cada cena e, se quiseres, os inícios exatos de cada frase (`inicios` na `Legenda`)

## Cenas 3D
Feitas com `@remotion/three` (Three.js + React Three Fiber), em `src/tres/`:

| Ficheiro | O quê |
|---|---|
| `Estadio.tsx` | Relvado às faixas, linhas com medidas reais, baliza com rede, painel LED com a marca, bancada com público |
| `Personagens.tsx` | Guarda-redes feito de formas simples (`mergulho` de 0 a 1, `lado`, `alcance`), bola, câmara controlada por frame, `projetar()` para pôr etiquetas HTML por cima do 3D |
| `cenas3d.tsx` | `Cena3DFrenteAFrente` (abertura) e `Cena3DESe` (defesa → rebobinar → guarda-redes médio → golo) |

Os remates e mergulhos são ilustrativos, não são lances reais.

O render 3D é mais lento (cerca de 4 minutos para 59 s num ambiente sem placa gráfica). Num computador normal é bem mais rápido.
Se aparecer "Error creating WebGL context", usa `--gl=swangle`:
```bash
npx remotion render Ep01 out/ep01.mp4 --gl=swangle
```

## Próximos passos
- Legendas automáticas a partir da voz (`@remotion/install-whisper-cpp`)

## Render num ambiente sem descarregar o browser
```bash
REMOTION_BROWSER=/caminho/para/chrome-headless-shell npm run render
```
