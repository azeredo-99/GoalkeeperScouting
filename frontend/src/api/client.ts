import type {
  BenchmarkResponse,
  ComparisonResponse,
  DataCoverageResponse,
  PerformanceRow,
  PlayerProfileResponse,
  ScoutingMatch,
  ScoutingProfile,
  SimilarityResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const GENERIC_ERROR = "Unable to load goalkeeper data. Please try again.";

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`);
  } catch {
    throw new Error("Unable to reach the scouting service. Check your connection and try again.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : undefined;
    // Only surface backend detail when it's already scout-facing prose, not
    // an internal validation string (those are humanized here instead).
    const humanized = detail && !detail.startsWith("Invalid selection") && !detail.startsWith("No performance for");
    throw new Error(humanized ? detail : GENERIC_ERROR);
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
  minSavePct?: number;
  minSweeperActionsP90?: number;
  minPassSuccessPct?: number;
  minLongBallPct?: number;
  scoutingProfileId?: string;
  // Definição completa de um perfil criado/editado pelo scout no browser
  // (localStorage, ver lib/customScoutingProfiles.ts) -- o backend nunca
  // guarda isto, só o reavalia por pedido, tal como os predefinidos.
  // Tem prioridade sobre `scoutingProfileId` quando ambos são passados.
  customProfile?: ScoutingProfile;
}

export function discoverPlayers(filters: DiscoverFilters): Promise<{ results: PerformanceRow[] }> {
  const params = new URLSearchParams();
  if (filters.competitionId !== undefined) params.set("competition_id", String(filters.competitionId));
  if (filters.seasonId !== undefined) params.set("season_id", String(filters.seasonId));
  if (filters.minMinutes !== undefined) params.set("min_minutes", String(filters.minMinutes));
  if (filters.maxAge !== undefined) params.set("max_age", String(filters.maxAge));
  if (filters.maxMarketValueEur !== undefined)
    params.set("max_market_value_eur", String(filters.maxMarketValueEur));
  if (filters.minSavePct !== undefined) params.set("min_save_pct", String(filters.minSavePct));
  if (filters.minSweeperActionsP90 !== undefined)
    params.set("min_sweeper_actions_p90", String(filters.minSweeperActionsP90));
  if (filters.minPassSuccessPct !== undefined)
    params.set("min_pass_success_pct", String(filters.minPassSuccessPct));
  if (filters.minLongBallPct !== undefined) params.set("min_long_ball_pct", String(filters.minLongBallPct));
  if (filters.customProfile !== undefined) {
    params.set("custom_profile", JSON.stringify(filters.customProfile));
  } else if (filters.scoutingProfileId !== undefined) {
    params.set("scouting_profile_id", filters.scoutingProfileId);
  }
  return getJson(`/api/players/discover?${params.toString()}`);
}

export function getScoutingProfiles(): Promise<{ profiles: ScoutingProfile[] }> {
  return getJson("/api/scouting-profiles");
}

export function getScoutingProfile(profileId: string): Promise<ScoutingProfile> {
  return getJson(`/api/scouting-profiles/${encodeURIComponent(profileId)}`);
}

export function getScoutingMatch(
  playerName: string,
  profileId: string,
  competitionId: number,
  seasonId: number
): Promise<ScoutingMatch> {
  const params = new URLSearchParams({
    profile_id: profileId,
    competition_id: String(competitionId),
    season_id: String(seasonId),
  });
  return getJson(`/api/players/${encodeURIComponent(playerName)}/scouting-match?${params.toString()}`);
}

export function getDataCoverage(): Promise<DataCoverageResponse> {
  return getJson("/api/data-coverage");
}

export interface NamedOption {
  id: number;
  name: string;
}

export function getCompetitions(): Promise<{ competitions: NamedOption[] }> {
  return getJson("/api/competitions");
}

export function getSeasons(competitionId?: number): Promise<{ seasons: NamedOption[] }> {
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

export function getPlayerBenchmark(
  playerName: string,
  competitionId: number,
  seasonId: number
): Promise<BenchmarkResponse> {
  const params = new URLSearchParams({
    competition_id: String(competitionId),
    season_id: String(seasonId),
  });
  return getJson(`/api/players/${encodeURIComponent(playerName)}/benchmark?${params.toString()}`);
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
