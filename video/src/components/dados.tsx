import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { MARCA } from "../marca";
import { formatar } from "./texto";

// Número que sobe de 0 até ao valor
export const Contador: React.FC<{
  valor: number;
  casas?: number;
  sinal?: boolean;
  sufixo?: string;
  atraso?: number;
  duracao?: number;
  tamanho?: number;
  cor?: string;
}> = ({ valor, casas = 0, sinal = false, sufixo = "", atraso = 0, duracao = 30, tamanho = 120, cor }) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame - atraso, [0, duracao], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <span
      style={{
        fontFamily: MARCA.fonteTitulo,
        fontWeight: 900,
        fontSize: tamanho,
        lineHeight: 1,
        color: cor ?? MARCA.cores.texto,
        fontVariantNumeric: "tabular-nums",
        letterSpacing: -2,
      }}
    >
      {formatar(valor * t, casas, sinal)}
      {sufixo}
    </span>
  );
};

export const Etiqueta: React.FC<{ children: React.ReactNode; cor?: string; tamanho?: number }> = ({
  children,
  cor,
  tamanho = 30,
}) => (
  <div
    style={{
      fontFamily: MARCA.fonteEtiqueta,
      fontWeight: 700,
      fontSize: tamanho,
      letterSpacing: 5,
      textTransform: "uppercase",
      color: cor ?? MARCA.cores.texto2,
    }}
  >
    {children}
  </div>
);

// Cartão com barra lateral na cor do jogador
export const Cartao: React.FC<{
  nome: string;
  cor: string;
  atraso?: number;
  children: React.ReactNode;
  largura?: number;
}> = ({ nome, cor, atraso = 0, children, largura = 440 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - atraso, fps, config: { damping: 18 } });
  return (
    <div
      style={{
        width: largura,
        background: MARCA.cores.cartao,
        border: `1px solid ${MARCA.cores.linha}`,
        borderLeft: `8px solid ${cor}`,
        borderRadius: 22,
        padding: "30px 34px",
        opacity: s,
        transform: `translateY(${(1 - s) * 60}px)`,
        boxShadow: "0 30px 60px rgba(0,0,0,0.45)",
      }}
    >
      <Etiqueta cor={cor}>{nome}</Etiqueta>
      <div style={{ marginTop: 16 }}>{children}</div>
    </div>
  );
};

// Grelha 10x10 em forma de rede de baliza: cada quadrado = 1%.
export const GrelhaRede: React.FC<{ pct: number; cor: string; atraso?: number; tamanho?: number }> = ({
  pct,
  cor,
  atraso = 0,
  tamanho = 34,
}) => {
  const frame = useCurrentFrame();
  const preenchido = interpolate(frame - atraso, [0, 45], [0, pct], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const gap = 5;
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(10, ${tamanho}px)`, gap }}>
      {Array.from({ length: 100 }).map((_, i) => {
        // enche de baixo para cima, como a bola a entrar na rede
        const linha = 9 - Math.floor(i / 10);
        const idx = linha * 10 + (i % 10);
        const f = Math.max(0, Math.min(1, preenchido - idx));
        return (
          <div
            key={i}
            style={{
              width: tamanho,
              height: tamanho,
              border: `2px solid ${f > 0 ? cor : "rgba(255,255,255,0.12)"}`,
              borderRadius: 4,
              background: `linear-gradient(90deg, ${cor} ${f * 100}%, transparent ${f * 100}%)`,
            }}
          />
        );
      })}
    </div>
  );
};
