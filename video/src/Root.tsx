import React from "react";
import { Composition, Series } from "remotion";
import { ALTURA, FPS, LARGURA } from "./marca";
import { Moldura } from "./components/Moldura";
import { Legenda } from "./components/Legenda";
import { Episodio } from "./episodios/tipos";
import { EP01 } from "./episodios/ep01";

const Video: React.FC<{ ep: Episodio }> = ({ ep }) => (
  <Series>
    {ep.cenas.map((c, i) => {
      const dur = Math.round(c.segundos * FPS);
      return (
        <Series.Sequence key={i} durationInFrames={dur}>
          <Moldura capitulo={i + 1} totalCapitulos={ep.cenas.length} etiqueta={c.etiqueta} titulo={c.titulo} fonte={ep.fonte}>
            {c.conteudo}
          </Moldura>
          <Legenda frases={c.legenda} duracao={dur} />
        </Series.Sequence>
      );
    })}
  </Series>
);

const Ep01: React.FC = () => <Video ep={EP01} />;

const duracao = (ep: Episodio) => ep.cenas.reduce((s, c) => s + Math.round(c.segundos * FPS), 0);

export const Root: React.FC = () => (
  <>
    <Composition id={EP01.id} component={Ep01} durationInFrames={duracao(EP01)}
      fps={FPS} width={LARGURA} height={ALTURA} />
  </>
);
