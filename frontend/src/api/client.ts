import type {
  ComparisonResponse,
  PerformanceRow,
  PlayerProfileResponse,
  SimilarityResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function searchPlayers(query: string): Promise<{ results: PerformanceRow[] }> {
  return getJson(`/api/players/search?q=${encodeURIComponent(query)}`);
}

export interface DiscoverFilters {
  competitionId?: number;
  seasonId?: number;
  minMinutes?: number;
  maxAge?: number;
  maxMarketValueEur?: number;
}

export function discoverPlayers(filters: DiscoverFilters): Promise<{ results: PerformanceRow[] }> {
  const params = new URLSearchParams();
  if (filters.competitionId !== undefined) params.set("competition_id", String(filters.competitionId));
  if (filters.seasonId !== undefined) params.set("season_id", String(filters.seasonId));
  if (filters.minMinutes !== undefined) params.set("min_minutes", String(filters.minMinutes));
  if (filters.maxAge !== undefined) params.set("max_age", String(filters.maxAge));
  if (filters.maxMarketValueEur !== undefined)
    params.set("max_market_value_eur", String(filters.maxMarketValueEur));
  return getJson(`/api/players/discover?${params.toString()}`);
}

export function getCompetitions(): Promise<{ competitions: number[] }> {
  return getJson("/api/competitions");
}

export function getSeasons(competitionId?: number): Promise<{ seasons: number[] }> {
  const params = competitionId !== undefined ? `?competition_id=${competitionId}` : "";
  return getJson(`/api/seasons${params}`);
}

export function getPlayerProfile(playerName: string): Promise<PlayerProfileResponse> {
  return getJson(`/api/players/${encodeURIComponent(playerName)}/performances`);
}

export function getComparison(
  selections: { playerName: string; competitionId: number; seasonId: number }[]
): Promise<ComparisonResponse> {
  const query = selections
    .map((s) => `${s.playerName}:${s.competitionId}:${s.seasonId}`)
    .join(",");
  return getJson(`/api/comparison?selections=${encodeURIComponent(query)}`);
}

export interface SimilarityWeights {
  shotStopping: number;
  distribution: number;
  proactivity: number;
}

export function getSimilarity(
  target: string,
  weights: SimilarityWeights,
  topN = 5
): Promise<SimilarityResponse> {
  const params = new URLSearchParams({
    target,
    w_shot_stopping: String(weights.shotStopping),
    w_distribution: String(weights.distribution),
    w_proactivity: String(weights.proactivity),
    top_n: String(topN),
  });
  return getJson(`/api/similarity?${params.toString()}`);
}
