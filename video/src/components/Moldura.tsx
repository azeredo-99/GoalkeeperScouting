import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { MARCA } from "../marca";
import { TextoDestaque } from "./texto";

type Props = {
  capitulo: number;
  totalCapitulos: number;
  etiqueta: string; // pequeno texto por cima do título, ex.: "O BÁSICO"
  titulo: string;
  fonte?: string;
  children: React.ReactNode;
};

// Ícone: baliza vista de frente (a marca da série)
const IconeBaliza: React.FC<{ tamanho?: number }> = ({ tamanho = 40 }) => (
  <svg width={tamanho} height={tamanho * 0.7} viewBox="0 0 40 28">
    <path d="M3 27 V3 H37 V27" fill="none" stroke={MARCA.cores.destaque} strokeWidth={3.5} />
    {[10, 17, 24, 31].map((x) => (
      <line key={x} x1={x} y1={5} x2={x} y2={27} stroke={MARCA.cores.destaque} strokeOpacity={0.35} strokeWidth={1.2} />
    ))}
    {[10, 17, 24].map((y) => (
      <line key={y} x1={5} y1={y} x2={35} y2={y} stroke={MARCA.cores.destaque} strokeOpacity={0.35} strokeWidth={1.2} />
    ))}
  </svg>
);

export const Moldura: React.FC<Props> = ({ capitulo, totalCapitulos, etiqueta, titulo, fonte, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entrada = spring({ frame, fps, config: { damping: 200 } });
  const c = MARCA.cores;

  return (
    <AbsoluteFill style={{ backgroundColor: c.fundo, fontFamily: MARCA.fonteTitulo, color: c.texto }}>
      {children}

      {/* cabeçalho: marca + progresso por capítulos */}
      <div style={{ position: "absolute", top: 150, left: 80, right: 80 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <IconeBaliza />
          <span style={{ fontFamily: MARCA.fonteEtiqueta, fontWeight: 700, fontSize: 30, letterSpacing: 4 }}>
            {MARCA.serie}
          </span>
          <span style={{ marginLeft: "auto", fontFamily: MARCA.fonteEtiqueta, fontSize: 28, color: c.texto2, letterSpacing: 2 }}>
            {MARCA.conta}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 22 }}>
          {Array.from({ length: totalCapitulos }).map((_, i) => (
            <div key={i} style={{ flex: 1, height: 6, borderRadius: 3, background: c.linha, overflow: "hidden" }}>
              <div
                style={{
                  height: "100%",
                  background: c.destaque,
                  width: i < capitulo - 1 ? "100%" : i === capitulo - 1 ? `${entrada * 100}%` : "0%",
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* título da secção */}
      {titulo ? <div
        style={{
          position: "absolute",
          top: 260,
          left: 80,
          right: 80,
          opacity: entrada,
          transform: `translateY(${interpolate(entrada, [0, 1], [30, 0])}px)`,
        }}
      >
        <div style={{ fontFamily: MARCA.fonteEtiqueta, fontWeight: 700, fontSize: 32, letterSpacing: 6, color: c.destaque }}>
          {String(capitulo).padStart(2, "0")} · {etiqueta}
        </div>
        <div style={{ fontWeight: 900, fontSize: 82, lineHeight: 1.02, marginTop: 10, letterSpacing: -1 }}>
          <TextoDestaque texto={titulo} />
        </div>
      </div> : null}

      {fonte ? (
        <div
          style={{
            position: "absolute",
            bottom: 140,
            left: 80,
            fontFamily: MARCA.fonteEtiqueta,
            fontSize: 24,
            letterSpacing: 2,
            color: c.texto2,
          }}
        >
          {fonte}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
