import React from "react";

export type Cena = {
  segundos: number;
  etiqueta: string; // texto pequeno por cima do título
  titulo: string; // título da secção; *palavra* = destaque
  legenda: string[]; // frases da voz; *palavra* = destaque
  conteudo: React.ReactNode;
  topoLegenda?: number; // posição vertical da legenda (px); por defeito 1300
};

export type Voz = {
  pasta: string; // dentro de public/, ex.: "voz/ep01"
  tempos: number[][]; // duração (s) de cada frase, por cena (gerado por voz/gerar_voz.py)
  inicioMinimo?: (number[] | undefined)[]; // opcional: segundos mínimos para começar cada frase
};

export type Episodio = {
  id: string;
  fonte: string;
  cenas: Cena[];
  voz?: Voz;
};
