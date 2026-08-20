// Formatação de apresentação apenas -- espelha gk_scouting.presentation
// (nunca recalcula uma métrica, só decide como um valor já calculado é
// mostrado). NaN/null nunca vira "0".

export const NO_ACTIONS_LABEL = "N/A — no recorded actions";

export function formatMetric(
  value: number | null | undefined,
  decimals = 1,
  suffix = "",
  empty = "N/A"
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return empty;
  return `${value.toFixed(decimals)}${suffix}`;
}

export const formatPct = (v: number | null | undefined, empty = "N/A") =>
  formatMetric(v, 1, "%", empty);

export const formatCount = (v: number | null | undefined, empty = "N/A") =>
  formatMetric(v, 0, "", empty);

export const formatRateP90 = (v: number | null | undefined, empty = "N/A") =>
  formatMetric(v, 2, "", empty);

export const formatDistance = (v: number | null | undefined, empty = "N/A") =>
  formatMetric(v, 1, " m", empty);

export function formatMarketValue(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  if (value >= 1_000_000) {
    const millions = value / 1_000_000;
    return millions >= 10 ? `€${millions.toFixed(0)}M` : `€${millions.toFixed(1)}M`;
  }
  if (value >= 1_000) return `€${(value / 1_000).toFixed(0)}K`;
  return `€${value.toFixed(0)}`;
}

export function contextLabel(competitionId: number, seasonId: number): string {
  return `Competition #${competitionId} · Season #${seasonId}`;
}
