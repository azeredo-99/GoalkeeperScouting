import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { MARCA } from "../marca";
import { partes } from "./texto";

// Legenda da voz: frases que entram palavra a palavra, no terço inferior.
// As palavras entre *asteriscos* ganham um bloco menta.
// Sem voz gravada, o tempo é dividido por igual entre as frases;
// quando gravares a voz, passa os inícios reais em `inicios` (em frames).
export const Legenda: React.FC<{
  frases: string[];
  duracao: number;
  inicios?: number[];
  duracoes?: number[]; // com voz: duração de cada frase, para as palavras entrarem ao ritmo da fala
  topo?: number;
}> = ({ frases, duracao, inicios, duracoes, topo = 1300 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ini = inicios ?? frases.map((_, i) => Math.round((i * duracao) / frases.length));
  let atual = 0;
  ini.forEach((f, i) => {
    if (frame >= f) atual = i;
  });
  const local = frame - ini[atual];

  const palavras: { texto: string; destaque: boolean }[] = [];
  // um destaque com várias palavras ("Rui Silva") fica num só bloco
  partes(frases[atual]).forEach((p) =>
    p.destaque
      ? palavras.push({ texto: p.texto.trim(), destaque: true })
      : p.texto
          .split(" ")
          .filter(Boolean)
          .forEach((w) => {
            // pontuação solta (",", ".") cola-se à palavra anterior
            if (/^[.,;:!?…]+$/.test(w) && palavras.length) palavras[palavras.length - 1].texto += w;
            else palavras.push({ texto: w, destaque: false });
          }),
  );

  // com voz, as palavras entram ao ritmo da frase; sem voz, de 3 em 3 frames
  const passo = duracoes ? Math.max(2, Math.min(8, (duracoes[atual] * 0.85) / Math.max(1, palavras.length))) : 3;

  return (
    <div
      style={{
        position: "absolute",
        top: topo,
        left: 70,
        right: 70,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: "10px 16px",
        fontFamily: MARCA.fonteTitulo,
        fontWeight: 800,
        fontSize: 62,
        textTransform: "uppercase",
        lineHeight: 1.1,
      }}
    >
      {palavras.map((w, i) => {
        const s = spring({ frame: local - i * passo, fps, config: { damping: 14, stiffness: 180 } });
        return (
          <span
            key={`${atual}-${i}`}
            style={{
              opacity: Math.min(1, s * 1.5),
              transform: `translateY(${(1 - s) * 24}px) scale(${0.9 + s * 0.1})`,
              padding: w.destaque ? "0 14px" : 0,
              background: w.destaque ? MARCA.cores.destaque : "transparent",
              color: w.destaque ? MARCA.cores.fundo : MARCA.cores.texto,
              borderRadius: 10,
              textShadow: w.destaque ? "none" : "0 4px 18px rgba(0,0,0,0.7)",
            }}
          >
            {w.texto}
          </span>
        );
      })}
    </div>
  );
};
