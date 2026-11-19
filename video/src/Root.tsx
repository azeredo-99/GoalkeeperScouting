import React from "react";
import { Audio, Composition, Sequence, Series, staticFile } from "remotion";
import { ALTURA, FPS, LARGURA } from "./marca";
import { Moldura } from "./components/Moldura";
import { Legenda } from "./components/Legenda";
import { Episodio } from "./episodios/tipos";
import { EP01 } from "./episodios/ep01";

// Ritmo da voz (segundos)
const ANTES = 0.35; // silêncio no início de cada cena
const ENTRE = 0.3; // pausa entre frases
const DEPOIS = 0.6; // silêncio no fim da cena

type Plano = { dur: number; inicios?: number[]; duracoes?: number[] };

// Com voz: a cena dura o que a voz precisa (nunca menos do que `segundos`)
// e cada legenda começa quando a frase começa.
const planear = (ep: Episodio): Plano[] =>
  ep.cenas.map((c, i) => {
    const base = Math.round(c.segundos * FPS);
    const tempos = ep.voz?.tempos[i];
    if (!tempos) return { dur: base };
    const minimos = ep.voz?.inicioMinimo?.[i] ?? [];
    const inicios: number[] = [];
    let fim = ANTES - ENTRE;
    tempos.forEach((d, j) => {
      const ini = Math.max(fim + ENTRE, minimos[j] ?? 0);
      inicios.push(ini);
      fim = ini + d;
    });
    return {
      dur: Math.max(base, Math.round((fim + DEPOIS) * FPS)),
      inicios: inicios.map((s) => Math.round(s * FPS)),
      duracoes: tempos.map((d) => Math.round(d * FPS)),
    };
  });

const Video: React.FC<{ ep: Episodio }> = ({ ep }) => {
  const plano = planear(ep);
  return (
    <Series>
      {ep.cenas.map((c, i) => {
        const p = plano[i];
        return (
          <Series.Sequence key={i} durationInFrames={p.dur}>
            <Moldura capitulo={i + 1} totalCapitulos={ep.cenas.length} etiqueta={c.etiqueta} titulo={c.titulo} fonte={ep.fonte}>
              {c.conteudo}
            </Moldura>
            <Legenda frases={c.legenda} duracao={p.dur} inicios={p.inicios} duracoes={p.duracoes} topo={c.topoLegenda} />
            {ep.voz && p.inicios
              ? p.inicios.map((ini, j) => (
                  <Sequence key={j} from={ini} layout="none">
                    <Audio src={staticFile(`${ep.voz!.pasta}/${i}_${j}.wav`)} />
                  </Sequence>
                ))
              : null}
          </Series.Sequence>
        );
      })}
    </Series>
  );
};

const Ep01: React.FC = () => <Video ep={EP01} />;

const duracao = (ep: Episodio) => planear(ep).reduce((s, p) => s + p.dur, 0);

export const Root: React.FC = () => (
  <>
    <Composition id={EP01.id} component={Ep01} durationInFrames={duracao(EP01)} fps={FPS} width={LARGURA} height={ALTURA} />
  </>
);
