import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { MARCA, LARGURA, ALTURA } from "../marca";
import { Estadio } from "./Estadio";
import { Bola, Camara, GuardaRedes3D, projetar } from "./Personagens";
import { Jogador, Rebobinar } from "../scenes/cenas";

type V3 = [number, number, number];
const lerp3 = (a: V3, b: V3, t: number): V3 => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const EtiquetaNome: React.FC<{ x: number; y: number; texto: string; cor: string; op?: number }> = ({ x, y, texto, cor, op = 1 }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      transform: "translate(-50%, 0)",
      opacity: op,
      padding: "8px 20px",
      background: cor,
      color: MARCA.cores.fundo,
      borderRadius: 8,
      fontFamily: MARCA.fonteEtiqueta,
      fontWeight: 700,
      fontSize: 32,
      letterSpacing: 4,
      whiteSpace: "nowrap",
      boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
    }}
  >
    {texto}
  </div>
);

// Escurece o topo para o título se ler bem por cima do estádio
const VeuTopo: React.FC = () => (
  <AbsoluteFill
    style={{ background: `linear-gradient(180deg, ${MARCA.cores.fundo} 0%, rgba(10,15,26,0.85) 22%, rgba(10,15,26,0) 40%)` }}
  />
);

// ---------------------------------------------------------------------------
// Cena 3D: os dois guarda-redes frente a frente, na linha de golo
// ---------------------------------------------------------------------------
export const Cena3DFrenteAFrente: React.FC<{ a: Jogador; b: Jogador; duracao?: number }> = ({ a, b, duracao = 150 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = interpolate(frame, [0, duracao], [0, 1], { ...clamp, easing: Easing.inOut(Easing.sin) });
  const pos: V3 = [Math.sin(t * Math.PI) * 0.9 - 0.45, 2.3 - t * 0.2, 14 - t * 1.6];
  const alvo: V3 = [0, 1.1, 0];
  const fov = 32;
  const jogadores = [
    { j: a, p: [-1.15, 0, 0.6] as V3 },
    { j: b, p: [1.15, 0, 0.6] as V3 },
  ];
  return (
    <AbsoluteFill>
      <ThreeCanvas width={LARGURA} height={ALTURA} shadows camera={{ fov, position: pos, near: 0.1, far: 200 }}>
        <Camara pos={pos} alvo={alvo} fov={fov} />
        <Estadio />
        {jogadores.map(({ j, p }, i) => {
          const s = spring({ frame: frame - i * 8, fps, config: { damping: 14 } });
          return (
            <GuardaRedes3D key={j.nome} cor={j.cor} posicao={[p[0], (1 - s) * -2.2, p[2]]} rotacaoY={i === 0 ? 0.25 : -0.25} />
          );
        })}
      </ThreeCanvas>
      <VeuTopo />
      {jogadores.map(({ j, p }, i) => {
        const e = projetar([p[0], 0, p[2]], pos, alvo, fov, LARGURA, ALTURA);
        const op = interpolate(frame, [14 + i * 8, 24 + i * 8], [0, 1], clamp);
        return <EtiquetaNome key={j.nome} x={e.x} y={e.y + 18} texto={j.nome.toUpperCase()} cor={j.cor} op={op} />;
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Cena 3D: "E se…?" — a defesa, rebobinar, e um guarda-redes médio no lugar dele
// ---------------------------------------------------------------------------
const INICIO: V3 = [-0.6, 0.11, 11];
const ALVO_BOLA: V3 = [2.85, 1.85, 0];
const REDE: V3 = [3.0, 1.5, -1.4];
const DESVIO: V3 = [4.8, 1.0, 1.8];

// Uma tentativa de remate: f = frames desde o início do remate
const remate = (f: number, defende: boolean, atrasoMergulho: number) => {
  const voo = interpolate(f, [6, 24], [0, 1], clamp);
  let bola: V3 = lerp3(INICIO, ALVO_BOLA, voo);
  bola = [bola[0], bola[1] + Math.sin(voo * Math.PI) * 0.5, bola[2]];
  if (f > 24) {
    const k = interpolate(f, [24, 38], [0, 1], { ...clamp, easing: Easing.out(Easing.quad) });
    bola = defende ? lerp3(ALVO_BOLA, DESVIO, k) : lerp3(ALVO_BOLA, REDE, k);
  }
  const mergulho = interpolate(f, [10 + atrasoMergulho, 26 + atrasoMergulho], [0, 1], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  return { bola, mergulho, rodar: f * 0.6 };
};

export const Cena3DESe: React.FC<{ guarda: Jogador; rotuloMedio?: string }> = ({ guarda, rotuloMedio = "GUARDA-REDES MÉDIO" }) => {
  const frame = useCurrentFrame();
  // fases: 0–44 defesa · 44–62 rebobinar · 62–110 remate contra o médio · resto: pausa
  const FIM1 = 44;
  const REB = 62;
  let fase: "defesa" | "rebobinar" | "medio";
  let f: number;
  if (frame < FIM1) {
    fase = "defesa";
    f = frame;
  } else if (frame < REB) {
    fase = "rebobinar";
    f = interpolate(frame, [FIM1, REB], [FIM1, 0]);
  } else {
    fase = "medio";
    f = frame - REB;
  }
  const medio = fase === "medio";
  const r = remate(f, !medio, medio ? 7 : 0);
  const pos: V3 = [-1.4 + frame * 0.004, 1.8, 12 - frame * 0.008];
  const alvo: V3 = [0.9, 1.15, 0];
  const fov = 40;
  const golo = medio ? interpolate(f, [26, 34], [0, 1], clamp) : 0;
  const etq = projetar([0, 0, 0.3], pos, alvo, fov, LARGURA, ALTURA);
  return (
    <AbsoluteFill>
      <ThreeCanvas width={LARGURA} height={ALTURA} shadows camera={{ fov, position: pos, near: 0.1, far: 200 }}>
        <Camara pos={pos} alvo={alvo} fov={fov} />
        <Estadio />
        <GuardaRedes3D
          cor={medio ? "#7D879B" : guarda.cor}
          texto={medio ? "?" : "GR"}
          posicao={[0, 0, 0.3]}
          mergulho={r.mergulho}
          lado={1}
          alcance={medio ? 1.25 : 1.95}
        />
        <Bola posicao={r.bola} rodar={r.rodar} />
      </ThreeCanvas>
      <VeuTopo />
      <EtiquetaNome
        x={etq.x}
        y={etq.y + 18}
        texto={medio ? rotuloMedio : guarda.nome.toUpperCase()}
        cor={medio ? "#7D879B" : guarda.cor}
        op={fase === "rebobinar" ? 0 : 1}
      />
      {golo > 0 ? (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", top: 120 }}>
          <div
            style={{
              fontFamily: MARCA.fonteTitulo,
              fontWeight: 900,
              fontSize: 220,
              letterSpacing: -4,
              color: "#FF4D6D",
              opacity: golo,
              transform: `scale(${0.7 + golo * 0.3})`,
              textShadow: "0 0 40px rgba(255,77,109,0.65)",
            }}
          >
            GOLO.
          </div>
        </AbsoluteFill>
      ) : null}
      {fase === "rebobinar" ? (
        <div style={{ position: "absolute", inset: 0 }}>
          <RebobinarFixo />
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

// Rebobinar sempre visível enquanto dura a fase
const RebobinarFixo: React.FC = () => <Rebobinar duracao={9999} />;
