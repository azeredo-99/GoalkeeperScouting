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

export interface PerformanceMetrics {
  shotStopping: ShotStopping;
  sweeping: Sweeping;
  distribution: Distribution;
}

export interface PerformanceRow {
  playerName: string;
  competitionId: number;
  seasonId: number;
  competitionName: string;
  seasonName: string;
  minutes: number | null;
  club: string | null;
  age: number | null;
  marketValueEur: number | null;
  metrics: PerformanceMetrics;
  scoutingMatch?: ScoutingMatch;
}

// Nunca inclui idade -- um jogador pode ter várias linhas de
// desempenho (competições/épocas diferentes), e "idade" só faz
// sentido ligada a UMA dessas épocas (ver PerformanceRow.age), nunca
// como valor único ao nível do jogador.
export interface PlayerIdentity {
  playerName: string;
  club: string | null;
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
  competitionName: string;
  seasonName: string;
  minutes: number | null;
  club: string | null;
  marketValueEur: number | null;
  similarityPct: number;
  explanation: string;
  metrics: PerformanceMetrics;
}

export interface SimilarityResponse {
  target: PlayerIdentity & {
    competitionId: number;
    seasonId: number;
    competitionName: string;
    seasonName: string;
    minutes: number | null;
    metrics: PerformanceMetrics;
  };
  results: SimilarityResult[];
}

export interface ComparisonResponse {
  players: PerformanceRow[];
}

export type BenchmarkStatus = "no_data" | "insufficient" | "small" | "normal";

export interface BenchmarkMetric {
  key: string;
  label: string;
  category: "Shot Stopping" | "Sweeping" | "Distribution";
  value: number | null;
  percentile: number | null;
  peerCount: number;
  status: BenchmarkStatus;
}

export interface BenchmarkResponse {
  competitionName: string;
  seasonName: string;
  minimumMinutes: number;
  totalPeerCount: number;
  available: boolean;
  metrics: BenchmarkMetric[];
}

// Scouting Profile -- a scout's template of what they're looking for.
// Never a rating of the player; the preferences are scout-defined.
export interface ScoutingPreference {
  metric: string;
  label: string;
  enabled: boolean;
  weight: number;
  minimum: number | null;
  maximum: number | null;
}

export interface ScoutingProfile {
  id: string;
  name: string;
  description: string;
  preferences: ScoutingPreference[];
}

export type MatchStatus = "matched" | "unmet" | "insufficient_data";

export interface MatchEvaluation {
  metric: string;
  label: string;
  status: MatchStatus;
  value: number | null;
  minimum: number | null;
  maximum: number | null;
  weight: number;
}

// PLAYER × PROFILE × CONTEXT -- never a standalone player rating.
export interface ScoutingMatch {
  profileId: string;
  profileName: string;
  matchedCount: number;
  unmetCount: number;
  insufficientCount: number;
  matchScore: number | null;
  evaluations: MatchEvaluation[];
}

export type CoverageStatus = "insufficient" | "limited" | "partial" | "strong";

export interface DataCoverageContext {
  competitionId: number;
  seasonId: number;
  competitionName: string;
  seasonName: string;
  totalGoalkeepers: number;
  benchmarkableGoalkeepers: number;
  status: CoverageStatus;
}

export interface DataCoverageResponse {
  minimumMinutes: number;
  contexts: DataCoverageContext[];
}
