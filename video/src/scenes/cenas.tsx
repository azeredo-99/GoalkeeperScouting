import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { MARCA } from "../marca";
import { Baliza, GuardaRedes, Relvado } from "../components/cena";
import { Cartao, Contador, Etiqueta, GrelhaRede } from "../components/dados";

export type Jogador = { nome: string; cor: string; numero: string };

const entrar = (frame: number, fps: number, atraso = 0) =>
  spring({ frame: frame - atraso, fps, config: { damping: 16 } });

// 1. Dois guarda-redes frente a frente, com a baliza atrás
export const CenaFrenteAFrente: React.FC<{ a: Jogador; b: Jogador }> = ({ a, b }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, 150], [1, 1.06]);
  return (
    <AbsoluteFill>
      <Relvado />
      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
        <div style={{ position: "absolute", top: 645, left: 90 }}>
          <Baliza largura={900} />
        </div>
        {[a, b].map((j, i) => {
          const s = entrar(frame, fps, i * 8);
          return (
            <div
              key={j.nome}
              style={{
                position: "absolute",
                top: 690,
                left: i === 0 ? 90 : 690,
                opacity: s,
                transform: `translateY(${(1 - s) * 80}px)`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              <GuardaRedes cor={j.cor} numero={j.numero} escala={1.15} espelhar={i === 1} />
              <div
                style={{
                  marginTop: 6,
                  padding: "8px 20px",
                  background: j.cor,
                  color: MARCA.cores.fundo,
                  borderRadius: 8,
                  fontFamily: MARCA.fonteEtiqueta,
                  fontWeight: 700,
                  fontSize: 32,
                  letterSpacing: 4,
                }}
              >
                {j.nome.toUpperCase()}
              </div>
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// 2. Cartão de abertura da série
export const CenaSerie: React.FC<{ episodio: string; tema: string; pergunta: string }> = ({ episodio, tema, pergunta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s1 = entrar(frame, fps, 0);
  const s2 = entrar(frame, fps, 8);
  const s3 = entrar(frame, fps, 16);
  return (
    <AbsoluteFill>
      <Relvado escurecer={0.6} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", textAlign: "center", top: -80 }}>
        <div style={{ opacity: s1 }}>
          <Etiqueta cor={MARCA.cores.destaque} tamanho={36}>{episodio}</Etiqueta>
        </div>
        <div style={{ fontWeight: 900, fontSize: 132, lineHeight: 0.95, marginTop: 24, transform: `scale(${0.8 + s2 * 0.2})`, opacity: s2 }}>
          {MARCA.serie.split(" ").map((p, i) => (
            <div key={i}>{p}</div>
          ))}
        </div>
        <div style={{ marginTop: 40, opacity: s3, padding: "12px 28px", border: `3px solid ${MARCA.cores.destaque}`, borderRadius: 12 }}>
          <Etiqueta cor={MARCA.cores.texto} tamanho={36}>{tema}</Etiqueta>
        </div>
        <div style={{ marginTop: 26, opacity: s3 }}>
          <Etiqueta tamanho={30}>{pergunta}</Etiqueta>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// 3. Um número grande
export const CenaNumero: React.FC<{ valor: number; casas?: number; rotulo: string }> = ({ valor, casas = 0, rotulo }) => (
  <AbsoluteFill>
    <Relvado escurecer={0.35} />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", textAlign: "center", top: 40 }}>
      <Contador valor={valor} casas={casas} tamanho={300} cor={MARCA.cores.destaque} duracao={40} />
      <div style={{ marginTop: 10 }}>
        <Etiqueta tamanho={38}>{rotulo}</Etiqueta>
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);

// 4. Cartões lado a lado: valor principal + valor secundário
export type LinhaCartao = { valor: number; casas?: number; sinal?: boolean; sufixo?: string; rotulo: string };
export const CenaCartoes: React.FC<{ a: Jogador; b: Jogador; principal: [LinhaCartao, LinhaCartao]; secundario?: [LinhaCartao, LinhaCartao]; nota?: string }> = ({
  a,
  b,
  principal,
  secundario,
  nota,
}) => (
  <AbsoluteFill>
    <Relvado escurecer={0.55} />
    <div style={{ position: "absolute", top: 700, left: 70, right: 70, display: "flex", justifyContent: "space-between" }}>
      {[a, b].map((j, i) => (
        <Cartao key={j.nome} nome={j.nome} cor={j.cor} atraso={i * 10} largura={455}>
          <Contador {...principal[i]} atraso={10 + i * 10} tamanho={130} />
          <Etiqueta>{principal[i].rotulo}</Etiqueta>
          {secundario ? (
            <div style={{ marginTop: 26, paddingTop: 22, borderTop: `1px solid ${MARCA.cores.linha}` }}>
              <Contador {...secundario[i]} atraso={25 + i * 10} tamanho={64} cor={MARCA.cores.texto2} />
              <Etiqueta tamanho={24}>{secundario[i].rotulo}</Etiqueta>
            </div>
          ) : null}
        </Cartao>
      ))}
    </div>
    {nota ? (
      <div style={{ position: "absolute", top: 1180, left: 80, right: 80, textAlign: "center" }}>
        <Etiqueta tamanho={26}>{nota}</Etiqueta>
      </div>
    ) : null}
  </AbsoluteFill>
);

// 5. Grelhas "rede": percentagem em 100 quadrados
export const CenaGrelhas: React.FC<{ a: Jogador; b: Jogador; pct: [number, number]; rotulo: string }> = ({ a, b, pct, rotulo }) => (
  <AbsoluteFill>
    <Relvado escurecer={0.6} />
    <div style={{ position: "absolute", top: 640, left: 50, right: 50, display: "flex", justifyContent: "space-between" }}>
      {[a, b].map((j, i) => (
        <Cartao key={j.nome} nome={j.nome} cor={j.cor} atraso={i * 6} largura={478}>
          <GrelhaRede pct={pct[i]} cor={j.cor} atraso={12 + i * 6} tamanho={33} />
          <div style={{ marginTop: 22, textAlign: "center" }}>
            <Contador valor={pct[i]} casas={1} sufixo="%" atraso={12 + i * 6} duracao={45} tamanho={92} cor={j.cor} />
            <Etiqueta tamanho={24}>{rotulo}</Etiqueta>
          </div>
        </Cartao>
      ))}
    </div>
  </AbsoluteFill>
);

// 6. Baliza por zonas: nem todos os remates valem o mesmo
export const CenaZonasBaliza: React.FC<{ zonas: number[][]; nota: string }> = ({ zonas, nota }) => (
  <AbsoluteFill>
    <Relvado escurecer={0.5} />
    <div style={{ position: "absolute", top: 760, left: 90 }}>
      <Baliza largura={900} zonas={zonas} atraso={10} />
    </div>
    <div style={{ position: "absolute", top: 1130, left: 80, right: 80, textAlign: "center" }}>
      <Etiqueta tamanho={26}>{nota}</Etiqueta>
    </div>
  </AbsoluteFill>
);

// 7. Veredicto: duas linhas, uma por métrica
export const CenaVeredicto: React.FC<{ linhas: { metrica: string; vencedor: Jogador; texto: string }[] }> = ({ linhas }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Relvado escurecer={0.65} />
      <div style={{ position: "absolute", top: 640, left: 70, right: 70, display: "flex", flexDirection: "column", gap: 30 }}>
        {linhas.map((l, i) => {
          const s = entrar(frame, fps, 10 + i * 20);
          return (
            <div
              key={i}
              style={{
                opacity: s,
                transform: `translateX(${(1 - s) * -80}px)`,
                background: MARCA.cores.cartao,
                border: `1px solid ${MARCA.cores.linha}`,
                borderLeft: `8px solid ${l.vencedor.cor}`,
                borderRadius: 22,
                padding: "28px 34px",
              }}
            >
              <Etiqueta>{l.metrica}</Etiqueta>
              <div style={{ fontWeight: 900, fontSize: 60, marginTop: 8, color: l.vencedor.cor }}>{l.vencedor.nome}</div>
              <div style={{ fontSize: 34, fontWeight: 600, marginTop: 6, color: MARCA.cores.texto2 }}>{l.texto}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Efeito "rebobinar": linhas de vídeo antigo + rótulo, nos primeiros frames da cena
export const Rebobinar: React.FC<{ rotulo?: string; duracao?: number }> = ({ rotulo = "◀◀ E SE…?", duracao = 24 }) => {
  const frame = useCurrentFrame();
  if (frame > duracao) return null;
  const op = interpolate(frame, [0, 4, duracao - 6, duracao], [0, 1, 1, 0]);
  const salto = (frame % 3) * 6 - 6;
  return (
    <AbsoluteFill style={{ opacity: op, pointerEvents: "none" }}>
      <AbsoluteFill
        style={{
          background: "repeating-linear-gradient(180deg, rgba(255,255,255,0.07) 0 3px, transparent 3px 7px)",
          transform: `translateY(${salto}px)`,
          mixBlendMode: "screen",
        }}
      />
      <AbsoluteFill style={{ background: "rgba(10,15,26,0.35)" }} />
      <div
        style={{
          position: "absolute",
          bottom: 260,
          left: 80,
          fontFamily: MARCA.fonteEtiqueta,
          fontWeight: 700,
          fontSize: 72,
          letterSpacing: 6,
          color: MARCA.cores.texto,
          textShadow: `4px 0 ${MARCA.cores.destaque}, -4px 0 #FF4D6D`,
        }}
      >
        {rotulo}
      </div>
    </AbsoluteFill>
  );
};

// Etiqueta de contexto (equipa · competição · época)
export const Contexto: React.FC<{ texto: string }> = ({ texto }) => (
  <div
    style={{
      display: "inline-block",
      padding: "10px 22px",
      background: "rgba(10,15,26,0.85)",
      border: `1px solid ${MARCA.cores.linha}`,
      borderRadius: 10,
      fontFamily: MARCA.fonteEtiqueta,
      fontWeight: 700,
      fontSize: 28,
      letterSpacing: 4,
    }}
  >
    {texto}
  </div>
);

// Contrafactual: "e se tivessem um guarda-redes médio?"
// barra inteira = golos esperados contra (xGOT); parte cheia = golos sofridos; o resto = golos evitados
export const CenaContrafactual: React.FC<{
  linhas: { jogador: Jogador; contexto: string; sofridos: number; evitados: number }[];
}> = ({ linhas }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const max = Math.max(...linhas.map((l) => l.sofridos + l.evitados));
  return (
    <AbsoluteFill>
      <Relvado escurecer={0.6} />
      <div
        style={{
          position: "absolute",
          top: 640,
          left: 60,
          right: 60,
          background: MARCA.cores.cartao,
          border: `1px solid ${MARCA.cores.linha}`,
          borderRadius: 22,
          padding: "34px 36px 40px",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 26 }}>
          <Etiqueta tamanho={26}>GOLOS QUE UM GUARDA-REDES MÉDIO SOFRERIA</Etiqueta>
        </div>
        {linhas.map((l, i) => {
          const esperados = l.sofridos + l.evitados;
          const t = interpolate(frame - 30 - i * 12, [0, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const extra = interpolate(frame - 70 - i * 12, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const s = spring({ frame: frame - 70 - i * 12, fps, config: { damping: 12 } });
          const wSofridos = (l.sofridos / max) * 100;
          const wEvitados = (l.evitados / max) * 100;
          return (
            <div key={i} style={{ marginTop: i ? 40 : 0 }}>
              <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
                <Etiqueta cor={l.jogador.cor}>{l.jogador.nome}</Etiqueta>
                <Etiqueta tamanho={22}>{l.contexto}</Etiqueta>
              </div>
              <div style={{ position: "relative", height: 56, marginTop: 12, borderRadius: 28, background: "rgba(255,255,255,0.06)" }}>
                <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${wSofridos * t}%`, background: l.jogador.cor, borderRadius: 28 }} />
                <div
                  style={{
                    position: "absolute",
                    left: `${wSofridos}%`,
                    top: 0,
                    bottom: 0,
                    width: `${wEvitados * extra}%`,
                    borderRadius: "0 28px 28px 0",
                    background: `repeating-linear-gradient(135deg, ${MARCA.cores.destaque} 0 10px, rgba(61,245,176,0.35) 10px 20px)`,
                  }}
                />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 12 }}>
                <div>
                  <Contador valor={l.sofridos} atraso={30 + i * 12} tamanho={56} />
                  <Etiqueta tamanho={22}>SOFRIDOS</Etiqueta>
                </div>
                <div style={{ textAlign: "right", opacity: s, transform: `scale(${0.6 + s * 0.4})`, transformOrigin: "right center" }}>
                  <Contador valor={l.evitados} casas={1} sinal atraso={70 + i * 12} tamanho={56} cor={MARCA.cores.destaque} />
                  <Etiqueta tamanho={22} cor={MARCA.cores.destaque}>EVITADOS</Etiqueta>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
