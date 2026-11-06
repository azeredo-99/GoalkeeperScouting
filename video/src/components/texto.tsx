import React from "react";
import { MARCA } from "../marca";

// "*palavra*" = palavra em destaque (cor menta)
export const partes = (t: string) =>
  t.split(/(\*[^*]+\*)/g).filter(Boolean).map((p) => ({
    texto: p.replace(/\*/g, ""),
    destaque: p.startsWith("*") && p.endsWith("*"),
  }));

export const TextoDestaque: React.FC<{ texto: string; cor?: string }> = ({ texto, cor }) => (
  <>
    {partes(texto).map((p, i) => (
      <span key={i} style={{ color: p.destaque ? cor ?? MARCA.cores.destaque : undefined }}>
        {p.texto}
      </span>
    ))}
  </>
);

export const formatar = (v: number, casas: number, sinal = false) => {
  const s = Math.abs(v).toLocaleString("pt-PT", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  });
  if (v < 0) return "−" + s;
  return (sinal ? "+" : "") + s;
};
