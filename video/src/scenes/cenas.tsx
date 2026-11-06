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
