import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { MARCA } from "../marca";

// Relvado em perspetiva (desenhado à mão, sem 3D): faixas que alargam para baixo + grande área
const HORIZONTE = 700;
const LINHA_GOLO = 985;
export const Relvado: React.FC<{ escurecer?: number }> = ({ escurecer = 0 }) => {
  const frame = useCurrentFrame();
  const c = MARCA.cores;
  // faixas: cada uma mais alta do que a anterior (efeito de perspetiva)
  const faixas: { y: number; h: number }[] = [];
  let y = HORIZONTE;
  let h = 40;
  while (y < 1920) {
    faixas.push({ y, h });
    y += h;
    h *= 1.28;
  }
  const brilho = 0.1 + Math.sin(frame / 20) * 0.02;
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{ position: "absolute" }}>
        <defs>
          <linearGradient id="ceu" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={c.fundo} />
            <stop offset="1" stopColor={c.fundo2} />
          </linearGradient>
          <radialGradient id="luz" cx="0.5" cy="0.55" r="0.5">
            <stop offset="0" stopColor={c.destaque} stopOpacity={brilho} />
            <stop offset="1" stopColor={c.destaque} stopOpacity={0} />
          </radialGradient>
        </defs>
        <rect width={1080} height={HORIZONTE} fill="url(#ceu)" />
        <rect y={HORIZONTE} width={1080} height={1920 - HORIZONTE} fill={c.relva} />
        {faixas.map((f, i) => (i % 2 ? <rect key={i} y={f.y} width={1080} height={f.h} fill={c.relva2} /> : null))}
        <g fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth={5}>
          <line x1={0} y1={LINHA_GOLO} x2={1080} y2={LINHA_GOLO} />
          <polygon points={`300,${LINHA_GOLO} 780,${LINHA_GOLO} 860,1120 220,1120`} />
          <polygon points={`90,${LINHA_GOLO} 990,${LINHA_GOLO} 1240,1500 -160,1500`} />
          <path d="M340 1500 Q540 1640 740 1500" />
        </g>
        <ellipse cx={540} cy={1300} rx={620} ry={420} fill="url(#luz)" />
      </svg>
      <AbsoluteFill style={{ background: `rgba(10,15,26,${escurecer})` }} />
    </AbsoluteFill>
  );
};

// Guarda-redes em estilo plano/geométrico
export const GuardaRedes: React.FC<{
  cor: string;
  numero: string;
  pose?: "pronto" | "mergulho";
  escala?: number;
  espelhar?: boolean;
}> = ({ cor, numero, pose = "pronto", escala = 1, espelhar = false }) => {
  const frame = useCurrentFrame();
  const respirar = Math.sin(frame / 9) * 4;
  const mergulho = pose === "mergulho" ? interpolate(frame, [0, 18], [0, -55], { extrapolateRight: "clamp" }) : 0;
  const pele = "#E2B48E";
  return (
    <svg
      width={260 * escala}
      height={420 * escala}
      viewBox="0 0 260 420"
      style={{ transform: `${espelhar ? "scaleX(-1)" : ""} rotate(${mergulho}deg)`, overflow: "visible" }}
    >
      <ellipse cx={130} cy={410} rx={95} ry={14} fill="rgba(0,0,0,0.35)" />
      <g transform={`translate(0 ${respirar})`}>
        {/* pernas */}
        <rect x={88} y={250} width={34} height={140} rx={14} fill="#1B2333" />
        <rect x={138} y={250} width={34} height={140} rx={14} fill="#1B2333" />
        <rect x={82} y={380} width={46} height={18} rx={8} fill="#0A0D14" />
        <rect x={134} y={380} width={46} height={18} rx={8} fill="#0A0D14" />
        {/* braços abertos (posição de expectativa) */}
        <rect x={22} y={120} width={30} height={120} rx={14} fill={cor} transform="rotate(28 37 120)" />
        <rect x={208} y={120} width={30} height={120} rx={14} fill={cor} transform="rotate(-28 223 120)" />
        <circle cx={18} cy={236} r={24} fill="#F4F6FA" />
        <circle cx={242} cy={236} r={24} fill="#F4F6FA" />
        {/* tronco */}
        <rect x={70} y={110} width={120} height={160} rx={36} fill={cor} />
        <text x={130} y={210} textAnchor="middle" fontSize={64} fontWeight={900} fill="rgba(10,15,26,0.75)"
          fontFamily={MARCA.fonteTitulo} transform={espelhar ? "translate(260 0) scale(-1 1)" : undefined}>
          {numero}
        </text>
        {/* cabeça */}
        <circle cx={130} cy={70} r={46} fill={pele} />
        <path d="M84 62 Q130 6 176 62 L176 50 Q130 -4 84 50 Z" fill="#2A1C14" />
      </g>
    </svg>
  );
};

// Baliza vista de frente; com `zonas`, mostra o valor de cada zona (ideia do xGOT)
export const Baliza: React.FC<{ largura?: number; zonas?: number[][]; atraso?: number }> = ({
  largura = 900,
  zonas,
  atraso = 0,
}) => {
  const frame = useCurrentFrame();
  const altura = largura * 0.36;
  const lin = zonas?.length ?? 0;
  const col = zonas?.[0]?.length ?? 0;
  return (
    <svg width={largura} height={altura + 20} viewBox={`0 0 ${largura} ${altura + 20}`}>
      {zonas?.map((row, r) =>
        row.map((v, cIdx) => {
          const k = r * col + cIdx;
          const op = interpolate(frame - atraso - k * 4, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const w = (largura - 24) / col;
          const h = (altura - 12) / lin;
          return (
            <g key={k} opacity={op}>
              <rect x={12 + cIdx * w} y={12 + r * h} width={w} height={h} fill={MARCA.cores.destaque} fillOpacity={0.08 + v * 0.75} />
              <text x={12 + cIdx * w + w / 2} y={12 + r * h + h / 2 + 18} textAnchor="middle" fontSize={50} fontWeight={900}
                fontFamily={MARCA.fonteTitulo} fill={v > 0.5 ? MARCA.cores.fundo : MARCA.cores.texto}>
                {v.toLocaleString("pt-PT", { minimumFractionDigits: 2 })}
              </text>
            </g>
          );
        }),
      )}
      {/* rede */}
      {Array.from({ length: 18 }).map((_, i) => (
        <line key={`v${i}`} x1={12 + (i * (largura - 24)) / 17} y1={12} x2={12 + (i * (largura - 24)) / 17} y2={altura}
          stroke="rgba(255,255,255,0.12)" strokeWidth={2} />
      ))}
      {Array.from({ length: 8 }).map((_, i) => (
        <line key={`h${i}`} x1={12} y1={12 + (i * (altura - 12)) / 7} x2={largura - 12} y2={12 + (i * (altura - 12)) / 7}
          stroke="rgba(255,255,255,0.12)" strokeWidth={2} />
      ))}
      <path d={`M10 ${altura + 10} V10 H${largura - 10} V${altura + 10}`} fill="none" stroke="#F4F6FA" strokeWidth={16} strokeLinejoin="round" />
    </svg>
  );
};
