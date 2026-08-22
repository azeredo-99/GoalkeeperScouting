import type { BenchmarkResponse, PerformanceRow } from "../api/types";
import { formatPct, formatRateP90 } from "./format";
import { sampleSize } from "../components/ContextBadge";

// Partilhado entre Player Profile e Scouting Report -- as duas páginas
// mostram exatamente as mesmas frases para o mesmo contexto, nunca
// lógica duplicada que possa divergir. Cada frase é factual sobre
// dados que já existem noutro sítio da página (a amostra, valores em
// falta, cobertura do benchmark) -- nunca um julgamento de futebol
// ("bom", "fraco", "elite"). Não há população de comparação global,
// por isso não há base para uma opinião, só para descrever a evidência.
export function buildTakeaways(
  active: PerformanceRow,
  contextsCount: number,
  benchmark: BenchmarkResponse | null
): string[] {
  const takeaways: string[] = [];

  if (active.metrics.shotStopping.savePct != null) {
    takeaways.push(`Saved ${formatPct(active.metrics.shotStopping.savePct)} of shots on target in this sample.`);
  }
  if (active.metrics.sweeping.sweeperActionsP90 != null) {
    takeaways.push(`Recorded ${formatRateP90(active.metrics.sweeping.sweeperActionsP90)} sweeping actions per 90.`);
  } else {
    takeaways.push("Sweeping data is unavailable for this sample.");
  }
  if (active.metrics.distribution.passSuccessPct != null) {
    takeaways.push(`Pass success is ${formatPct(active.metrics.distribution.passSuccessPct)}.`);
  }

  const sampleTier = sampleSize(active.minutes);
  const sampleTierLabel = sampleTier === "large" ? "strong" : sampleTier === "medium" ? "moderate" : "limited";
  takeaways.push(
    `Performance sample contains ${active.minutes != null ? active.minutes.toFixed(0) : "0"} minutes (${sampleTierLabel}).`
  );

  if (benchmark) {
    takeaways.push(
      benchmark.available
        ? `${benchmark.totalPeerCount} comparable goalkeepers have sufficient data for benchmarking.`
        : "Not enough comparable goalkeepers are available for benchmarking in this competition/season."
    );
  }

  if (contextsCount > 1) {
    takeaways.push(`${contextsCount} performance contexts are available for this goalkeeper.`);
  }

  return takeaways;
}
