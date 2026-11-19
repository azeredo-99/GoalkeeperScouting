// Episódio 01: Rui Silva vs Kaique
// Dados: FotMob, Liga Portugal 2025/26 (ver content/dados/fotmob_liga_portugal_2025_26.csv)
import React from "react";
import { Episodio } from "./tipos";
import T from "./ep01.texto.json";
import V from "./ep01.voz.json";
import { Cena3DESe, Cena3DFrenteAFrente } from "../tres/cenas3d";
import {
  CenaCartoes,
  CenaContrafactual,
  CenaGrelhas,
  CenaNumero,
  CenaSerie,
  CenaVeredicto,
  CenaZonasBaliza,
  Jogador,
} from "../scenes/cenas";

const RUI: Jogador = { nome: "Rui Silva", cor: "#4FA3FF", numero: "GR" };
const KAIQUE: Jogador = { nome: "Kaique", cor: "#FF8A3D", numero: "GR" };

// Defesas e remates enquadrados (defesas + golos sofridos), época 2025/26
const D = {
  rui: { defesas: 76, remates: 99, pct: 76.8, ge: 3.5, ge90: 0.11 },
  kaique: { defesas: 87, remates: 122, pct: 71.3, ge: 4.9, ge90: 0.17 },
};

export const EP01: Episodio = {
  id: "Ep01",
  fonte: "DADOS: FOTMOB · LIGA PORTUGAL 2025/26",
  voz: {
    pasta: "voz/ep01",
    tempos: V,
    inicioMinimo: T.map((t) => (t as { inicioMinimo?: number[] }).inicioMinimo),
  },
  cenas: [
    {
      segundos: 5,
      etiqueta: "A DISCUSSÃO",
      titulo: "Quem merece a baliza do *Sporting*?",
      legenda: T[0].legenda,
      conteudo: <Cena3DFrenteAFrente a={RUI} b={KAIQUE} duracao={150} />,
      topoLegenda: 1400,
    },
    {
      segundos: 3,
      etiqueta: "EPISÓDIO 01",
      titulo: "",
      legenda: T[1].legenda,
      conteudo: <CenaSerie episodio="EPISÓDIO 01" tema="RUI SILVA vs KAIQUE" pergunta="QUEM É O N.º 1?" />,
    },
    {
      segundos: 4,
      etiqueta: "A AMOSTRA",
      titulo: "*221* remates à baliza",
      legenda: T[2].legenda,
      conteudo: <CenaNumero valor={D.rui.remates + D.kaique.remates} rotulo="REMATES ENQUADRADOS ANALISADOS" />,
    },
    {
      segundos: 6,
      etiqueta: "O BÁSICO",
      titulo: "Remates *defendidos*",
      legenda: T[3].legenda,
      conteudo: (
        <CenaCartoes
          a={RUI}
          b={KAIQUE}
          principal={[
            { valor: D.rui.defesas, rotulo: "DEFESAS" },
            { valor: D.kaique.defesas, rotulo: "DEFESAS" },
          ]}
          secundario={[
            { valor: D.rui.remates, rotulo: "REMATES ENQUADRADOS" },
            { valor: D.kaique.remates, rotulo: "REMATES ENQUADRADOS" },
          ]}
          nota="O KAIQUE FOI TESTADO MUITO MAIS VEZES"
        />
      ),
    },
    {
      segundos: 6,
      etiqueta: "PERCENTAGEM",
      titulo: "Defesas *%*",
      legenda: T[4].legenda,
      conteudo: <CenaGrelhas a={RUI} b={KAIQUE} pct={[D.rui.pct, D.kaique.pct]} rotulo="DOS REMATES DEFENDIDOS" />,
    },
    {
      segundos: 6,
      etiqueta: "O PROBLEMA",
      titulo: "Nem todos os remates são *iguais*",
      legenda: T[5].legenda,
      conteudo: (
        <CenaZonasBaliza
          zonas={[
            [0.72, 0.35, 0.74],
            [0.55, 0.12, 0.57],
            [0.64, 0.2, 0.66],
          ]}
          nota="PROBABILIDADE DE GOLO POR ZONA · VALORES ILUSTRATIVOS"
        />
      ),
    },
    {
      segundos: 6,
      etiqueta: "A MÉTRICA CERTA",
      titulo: "Golos *evitados*",
      legenda: T[6].legenda,
      conteudo: (
        <CenaCartoes
          a={RUI}
          b={KAIQUE}
          principal={[
            { valor: D.rui.ge, casas: 1, sinal: true, rotulo: "GOLOS EVITADOS" },
            { valor: D.kaique.ge, casas: 1, sinal: true, rotulo: "GOLOS EVITADOS" },
          ]}
          nota="BASEADO EM xGOT (QUALIDADE DO REMATE À BALIZA)"
        />
      ),
    },
    {
      segundos: 5,
      etiqueta: "E SE…?",
      titulo: "E se fosse um guarda-redes *médio*?",
      legenda: T[7].legenda,
      conteudo: <Cena3DESe guarda={KAIQUE} />,
      topoLegenda: 1400,
    },
    {
      segundos: 6,
      etiqueta: "A CONTA",
      titulo: "Golos que *valeram*",
      legenda: T[8].legenda,
      conteudo: (
        <CenaContrafactual
          linhas={[
            { jogador: RUI, contexto: "SPORTING · 2025/26", sofridos: 23, evitados: D.rui.ge },
            { jogador: KAIQUE, contexto: "NACIONAL · 2025/26", sofridos: 35, evitados: D.kaique.ge },
          ]}
        />
      ),
    },
    {
      segundos: 5,
      etiqueta: "POR JOGO",
      titulo: "Por *90 minutos*",
      legenda: T[9].legenda,
      conteudo: (
        <CenaCartoes
          a={RUI}
          b={KAIQUE}
          principal={[
            { valor: D.rui.ge90, casas: 2, sinal: true, rotulo: "GOLOS EVITADOS / 90" },
            { valor: D.kaique.ge90, casas: 2, sinal: true, rotulo: "GOLOS EVITADOS / 90" },
          ]}
        />
      ),
    },
    {
      segundos: 7,
      etiqueta: "VEREDICTO",
      titulo: "Os dois lados têm *razão*",
      legenda: T[10].legenda,
      conteudo: (
        <CenaVeredicto
          linhas={[
            { metrica: "DEFESAS %", vencedor: RUI, texto: "Defende mais dos remates que lhe chegam" },
            { metrica: "GOLOS EVITADOS / 90", vencedor: KAIQUE, texto: "Evita mais golos do que o esperado" },
          ]}
        />
      ),
    },
  ],
};
