export interface ShotStopping {
  savePct: number | null;
  shotsFaced: number | null;
  shotsSaved: number | null;
  goalsConceded: number | null;
  shotsFacedP90: number | null;
}

export interface Sweeping {
  sweeperActions: number | null;
  sweeperActionsP90: number | null;
  avgDistanceFromGoal: number | null;
  maxDistanceFromGoal: number | null;
}

export interface Distribution {
  passSuccessPct: number | null;
  totalPasses: number | null;
  avgPassLength: number | null;
  longBallPct: number | null;
}

export interface PerformanceRow {
  playerName: string;
  competitionId: number;
  seasonId: number;
  minutes: number | null;
  club: string | null;
  marketValueEur: number | null;
  metrics: {
    shotStopping: ShotStopping;
    sweeping: Sweeping;
    distribution: Distribution;
  };
}

export interface PlayerIdentity {
  playerName: string;
  club: string | null;
  age: number | null;
  marketValueEur: number | null;
  highestMarketValueEur: number | null;
}

export interface PlayerProfileResponse {
  identity: PlayerIdentity;
  performances: PerformanceRow[];
}

export interface SimilarityResult {
  rank: number;
  playerName: string;
  competitionId: number;
  seasonId: number;
  minutes: number | null;
  club: string | null;
  marketValueEur: number | null;
  similarityPct: number;
  explanation: string;
}

export interface SimilarityResponse {
  target: PlayerIdentity & { competitionId: number; seasonId: number; minutes: number | null };
  results: SimilarityResult[];
}

export interface ComparisonResponse {
  players: PerformanceRow[];
}
