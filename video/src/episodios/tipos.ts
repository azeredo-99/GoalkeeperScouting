import React from "react";

export type Cena = {
  segundos: number;
  etiqueta: string; // texto pequeno por cima do título
  titulo: string; // título da secção; *palavra* = destaque
  legenda: string[]; // frases da voz; *palavra* = destaque
  conteudo: React.ReactNode;
};

export type Episodio = {
  id: string;
  fonte: string;
  cenas: Cena[];
};
