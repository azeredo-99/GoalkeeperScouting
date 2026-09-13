import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getPlayerBenchmark, getPlayerProfile, getScoutingMatch, getSimilarity } from "../api/client";
import type {
  BenchmarkResponse,
  MatchEvaluation,
  PerformanceRow,
  PlayerProfileResponse,
  ScoutingMatch,
  SimilarityResponse,
} from "../api/types";
import { SampleIndicator, SourceBadge } from "../components/ContextBadge";
import { BenchmarkSection } from "../components/Benchmark";
import { DimensionSnapshot } from "../components/DimensionSnapshot";
import { MetricCard, MetricGroup } from "../components/MetricGroup";
import { RadarChart } from "../components/RadarChart";
import { SweeperMap } from "../components/SweeperMap";
import { ErrorState, LoadingState } from "../components/States";
import { addToShortlist, PRIORITY_LABELS, STATUS_LABELS, useShortlist } from "../lib/shortlist";
import { useCustomProfiles } from "../lib/customScoutingProfiles";
import { buildTakeaways } from "../lib/takeaways";
import {
  NO_ACTIONS_LABEL,
  formatClub,
  formatCount,
  formatDistance,
  formatMarketValue,
  formatPct,
  formatRateP90,
} from "../lib/format";

const RADAR_LABELS = ["Save %", "Sweeper /90", "Distance", "Pass %", "Long ball %"];

function radarValues(row: PerformanceRow): number[] {
  return [
    row.metrics.shotStopping.savePct ?? NaN,
    row.metrics.sweeping.sweeperActionsP90 ?? NaN,
    row.metrics.sweeping.avgDistanceFromGoal ?? NaN,
    row.metrics.distribution.passSuccessPct ?? NaN,
    row.metrics.distribution.longBallPct ?? NaN,
  ];
}

// Ficha de scouting -- uma composição das capacidades já existentes
// (Player Profile, Benchmark, Similarity, Shortlist), nunca uma
// arquitetura nova. Relativa a UM performance context específico,
// nunca uma média entre seasons -- por isso não há seletor de contexto
// aqui: o contexto vem da query string (preservado a partir do Profile)
// e, na falta dela, cai para a amostra de mais minutos.
export function ScoutingReport() {
  const { player } = useParams<{ player: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [data, setData] = useState<PlayerProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!player) return;
    setLoading(true);
    setError(null);
    getPlayerProfile(player)
      .then(setData)
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [player]);

  const active = useMemo(() => {
    if (!data) return null;
    const competitionId = Number(searchParams.get("competition_id"));
    const seasonId = Number(searchParams.get("season_id"));
    const requested = data.performances.find(
      (p) => p.competitionId === competitionId && p.seasonId === seasonId
    );
    return requested ?? data.performances[0] ?? null;
  }, [data, searchParams]);

  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  useEffect(() => {
    if (!active) return;
    setBenchmark(null);
    setBenchmarkLoading(true);
    getPlayerBenchmark(active.playerName, active.competitionId, active.seasonId)
      .then(setBenchmark)
      .catch(() => setBenchmark(null))
      .finally(() => setBenchmarkLoading(false));
  }, [active?.playerName, active?.competitionId, active?.seasonId]);

  const [similar, setSimilar] = useState<SimilarityResponse | null>(null);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [similarUnavailable, setSimilarUnavailable] = useState(false);

  useEffect(() => {
    if (!player) return;
    setSimilar(null);
    setSimilarUnavailable(false);
    setSimilarLoading(true);
    getSimilarity(player, { shotStopping: 30, distribution: 35, proactivity: 35 }, 3)
      .then(setSimilar)
      .catch(() => setSimilarUnavailable(true))
      .finally(() => setSimilarLoading(false));
  }, [player]);

  const shortlist = useShortlist();
  const shortlistEntry = data ? shortlist.find((e) => e.playerName === data.identity.playerName) : undefined;

  // Contexto de scouting opcional, vindo só da query string (ex.:
  // /report/Foo?scouting_profile=high-line-sweeper), nunca de um campo
  // gravado no jogador -- PLAYER × PROFILE × CONTEXT também aqui.
  const scoutingProfileId = searchParams.get("scouting_profile");
  const [scoutingMatch, setScoutingMatch] = useState<ScoutingMatch | null>(null);

  // O id na URL pode ser um predefinido (backend, ver get_profile) ou
  // um perfil custom do scout (localStorage) -- resolvido aqui, tal
  // como em Discover.tsx, para saber se enviamos só o id ou a
  // definição completa.
  const customProfiles = useCustomProfiles();
  const customProfile = useMemo(
    () => customProfiles.find((p) => p.id === scoutingProfileId) ?? undefined,
    [customProfiles, scoutingProfileId]
  );

  useEffect(() => {
    if (!scoutingProfileId || !active) {
      setScoutingMatch(null);
      return;
    }
    let cancelled = false;
    getScoutingMatch(active.playerName, scoutingProfileId, active.competitionId, active.seasonId, customProfile)
      .then((result) => {
        if (!cancelled) setScoutingMatch(result);
      })
      .catch(() => {
        if (!cancelled) setScoutingMatch(null);
      });
    return () => {
      cancelled = true;
    };
  }, [scoutingProfileId, active?.playerName, active?.competitionId, active?.seasonId, customProfile]);

  if (loading) return <LoadingState label="Loading report…" />;
  if (error) return <ErrorState message={error} />;
  if (!data || !active) return null;

  const { identity } = data;
  const takeaways = buildTakeaways(active, data.performances.length, benchmark);

  return (
    <div className="scouting-report">
      {/* Screen-only actions -- hidden entirely on print via .no-print */}
      <div className="no-print" style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-5)" }}>
        <button
          onClick={() => navigate(`/player/${encodeURIComponent(identity.playerName)}`)}
          style={btnSecondary}
        >
          ← Back to profile
        </button>
        <button onClick={() => window.print()} style={btnSecondary}>
          Print report
        </button>
      </div>

      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: "var(--color-text-tertiary)", marginBottom: 4 }}>
        GOALKEEPER SCOUTING REPORT
      </div>
      <h1 style={{ fontSize: 28, fontWeight: 800, margin: "0 0 var(--space-5)" }}>{identity.playerName}</h1>

      {/* SCOUTING PROFILE MATCH -- only present when the report was opened
          from a profile context (?scouting_profile=...). Every line here
          traces to an evaluated preference from the backend; nothing here
          is generated prose. */}
      {scoutingProfileId && scoutingMatch && (
        <div className="card report-section" style={{ marginBottom: "var(--space-5)" }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: "var(--color-text-tertiary)", marginBottom: 4 }}>
            SCOUTING PROFILE
          </div>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: "var(--space-3)" }}>
            {scoutingMatch.profileName}
            {scoutingMatch.matchScore != null && (
              <span className="tabular" style={{ marginLeft: 10, fontSize: 13, fontWeight: 700, color: "var(--color-accent-text)" }}>
                {scoutingMatch.matchScore.toFixed(0)}% match
              </span>
            )}
          </div>

          <div className="section-title">Match evidence</div>
          <ul style={{ margin: "0 0 var(--space-4)", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 4 }}>
            {scoutingMatch.evaluations.map((e) => (
              <li key={e.metric} style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: evidenceColor(e.status), fontWeight: 700 }}>{evidenceMark(e.status)}</span>
                <span>{e.label}</span>
                <span className="tabular" style={{ color: "var(--color-text-secondary)", marginLeft: "auto" }}>
                  {evidenceValue(e)}
                </span>
              </li>
            ))}
          </ul>

          <div className="section-title">Questions to investigate</div>
          {scoutingMatch.unmetCount === 0 && scoutingMatch.insufficientCount === 0 ? (
            <div style={{ fontSize: 12, color: "var(--color-text-tertiary)" }}>
              No unmet preferences or missing data for this profile in this context.
            </div>
          ) : (
            <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 4 }}>
              {scoutingMatch.evaluations
                .filter((e) => e.status !== "matched")
                .map((e) => (
                  <li key={e.metric} style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
                    — {questionFor(e)}
                  </li>
                ))}
            </ul>
          )}
        </div>
      )}

      {/* PLAYER HEADER + PERFORMANCE CONTEXT */}
      <div
        className="report-section"
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-4)", marginBottom: "var(--space-5)" }}
      >
        <div className="card">
          <div className="section-title">Current player information</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "var(--space-3)" }}>
            <div>
              <div className="label">Position</div>
              <div style={{ fontSize: 15, fontWeight: 700 }}>Goalkeeper</div>
            </div>
            <div>
              <div className="label">Age (this season)</div>
              <div className="tabular" style={{ fontSize: 15, fontWeight: 700 }}>
                {active.age != null ? `${active.age}` : "N/A"}
              </div>
            </div>
            <div>
              <div className="label">Club</div>
              <div style={{ fontSize: 15, fontWeight: 700 }}>{formatClub(identity.club)}</div>
            </div>
            <div>
              <div className="label">Market value</div>
              <div className="tabular" style={{ fontSize: 15, fontWeight: 700 }}>
                {formatMarketValue(identity.marketValueEur)}
              </div>
            </div>
            <div>
              <div className="label">Peak market value</div>
              <div className="tabular" style={{ fontSize: 15, fontWeight: 700 }}>
                {formatMarketValue(identity.highestMarketValueEur)}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="section-title">Performance context</div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ fontSize: 16, fontWeight: 700 }}>{active.competitionName}</div>
            {active.source === "fbref" && <SourceBadge />}
          </div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: "var(--space-3)" }}>
            {active.seasonName}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
            <div>
              <div className="label">Minutes</div>
              <div className="tabular" style={{ fontSize: 15, fontWeight: 700 }}>
                {active.minutes != null ? active.minutes.toFixed(0) : "N/A"}
              </div>
            </div>
            <SampleIndicator minutes={active.minutes} />
          </div>
        </div>
      </div>

      {/* SCOUTING SNAPSHOT */}
      <div className="card report-section" style={{ marginBottom: "var(--space-4)" }}>
        <div className="section-title">Scouting snapshot</div>
        <DimensionSnapshot metrics={active.metrics} />
      </div>

      {/* SCOUTING TAKEAWAYS */}
      <div className="report-section" style={{ marginBottom: "var(--space-5)" }}>
        <div className="section-title">Scouting takeaways</div>
        <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 4 }}>
          {takeaways.map((t) => (
            <li key={t} style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
              — {t}
            </li>
          ))}
        </ul>
      </div>

      {/* PERFORMANCE EVIDENCE */}
      <MetricGroup title="Shot Stopping">
        <MetricCard label="Save %" value={formatPct(active.metrics.shotStopping.savePct)} hint="Percentage of shots on target saved in this sample." />
        <MetricCard label="Shots faced" value={formatCount(active.metrics.shotStopping.shotsFaced)} hint="Total shots faced, on target or not." />
        <MetricCard label="Shots saved" value={formatCount(active.metrics.shotStopping.shotsSaved)} hint="Shots stopped by the goalkeeper." />
        <MetricCard label="Goals conceded" value={formatCount(active.metrics.shotStopping.goalsConceded)} hint="Goals conceded from shots faced." />
        <MetricCard label="Shots faced /90" value={formatRateP90(active.metrics.shotStopping.shotsFacedP90)} hint="Shots faced, normalised to a 90-minute rate." />
      </MetricGroup>

      <MetricGroup title="Sweeping" note="Absence of actions is not the same as zero.">
        <MetricCard label="Actions" value={formatCount(active.metrics.sweeping.sweeperActions, NO_ACTIONS_LABEL)} hint="Actions taken outside the box as a sweeper-keeper." />
        <MetricCard label="Actions /90" value={formatRateP90(active.metrics.sweeping.sweeperActionsP90, NO_ACTIONS_LABEL)} hint="Sweeper actions, normalised to a 90-minute rate." />
        <MetricCard label="Avg. distance" value={formatDistance(active.metrics.sweeping.avgDistanceFromGoal, NO_ACTIONS_LABEL)} hint="Average distance from goal for sweeper actions." />
        <MetricCard label="Max distance" value={formatDistance(active.metrics.sweeping.maxDistanceFromGoal, NO_ACTIONS_LABEL)} hint="Furthest sweeper action from goal in this sample." />
      </MetricGroup>

      <MetricGroup title="Distribution">
        <MetricCard label="Pass success" value={formatPct(active.metrics.distribution.passSuccessPct)} hint="Percentage of passes completed successfully." />
        <MetricCard label="Total passes" value={formatCount(active.metrics.distribution.totalPasses)} hint="Total passes attempted." />
        <MetricCard label="Avg. pass length" value={formatDistance(active.metrics.distribution.avgPassLength)} hint="Average distance of each pass." />
        <MetricCard label="Long ball %" value={formatPct(active.metrics.distribution.longBallPct)} hint="Percentage of passes longer than 40 metres." />
      </MetricGroup>

      {/* BENCHMARK */}
      <div className="report-section">
        <BenchmarkSection benchmark={benchmark} loading={benchmarkLoading} error={null} />
      </div>

      {/* VISUAL PROFILE */}
      <div className="section-title">Visual profile</div>
      <div className="report-section" style={{ display: "flex", gap: "var(--space-6)", flexWrap: "wrap", marginBottom: "var(--space-5)" }}>
        <div style={{ flex: "0 0 auto" }}>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8 }}>Performance radar</div>
          <RadarChart
            labels={RADAR_LABELS}
            series={[{ name: identity.playerName, color: "#22936b", values: radarValues(active) }]}
            emptyMessage="Not enough recorded metrics for a radar in this sample."
            size={200}
          />
        </div>
        <div style={{ flex: "1 1 240px", maxWidth: 320 }}>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8 }}>Sweeper map</div>
          <SweeperMap height={200} />
        </div>
      </div>

      {/* SIMILAR GOALKEEPERS -- reuses the algorithm's output exactly as
          returned; no recomputation. Explicitly labelled as model-based,
          never mixed with the facts/notes above. */}
      <div className="report-section" style={{ marginBottom: "var(--space-5)" }}>
        <div className="section-title">Similar goalkeepers</div>
        <div style={{ fontSize: 10, color: "var(--color-text-tertiary)", marginBottom: "var(--space-3)" }}>
          Model-based output (similarity algorithm) — not a scout judgement.
        </div>
        {similarLoading && <LoadingState label="Loading similar goalkeepers…" />}
        {!similarLoading && (similarUnavailable || !similar || similar.results.length === 0) && (
          <div style={{ fontSize: 12, color: "var(--color-text-tertiary)" }}>
            No comparable goalkeepers available for this sample.
          </div>
        )}
        {!similarLoading && similar && similar.results.length > 0 && (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
              {similar.results.slice(0, 3).map((r) => (
                <div
                  key={`${r.playerName}-${r.competitionId}-${r.seasonId}`}
                  className="card"
                  style={{
                    padding: "var(--space-3) var(--space-4)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "var(--space-4)",
                    flexWrap: "wrap",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{r.playerName}</div>
                    <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{formatClub(r.club)}</div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
                    <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
                      Save % <span className="tabular" style={{ color: "var(--color-text)", fontWeight: 700 }}>{formatPct(r.metrics.shotStopping.savePct)}</span>
                    </span>
                    <div style={{ textAlign: "right" }}>
                      <div className="label">Similarity</div>
                      <div className="tabular" style={{ fontSize: 15, fontWeight: 800, color: "var(--color-accent-text)" }}>
                        {r.similarityPct.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button
              className="no-print"
              onClick={() => navigate(`/similar/${encodeURIComponent(identity.playerName)}`)}
              style={btnSecondary}
            >
              View full similarity analysis
            </button>
          </>
        )}
      </div>

      {/* SCOUT NOTES -- manual entries from the Shortlist store. Kept
          visually separate from the facts above: this is the scout's
          own annotation, never a calculated value. */}
      <div
        className="card report-section"
        style={{ marginBottom: "var(--space-5)", borderStyle: shortlistEntry ? "solid" : "dashed" }}
      >
        <div className="section-title">Scout notes</div>
        {shortlistEntry ? (
          <>
            <div style={{ display: "flex", gap: "var(--space-6)", marginBottom: "var(--space-3)" }}>
              <div>
                <div className="label">Priority</div>
                <div style={{ fontSize: 14, fontWeight: 700 }}>{PRIORITY_LABELS[shortlistEntry.priority]}</div>
              </div>
              <div>
                <div className="label">Status</div>
                <div style={{ fontSize: 14, fontWeight: 700 }}>{STATUS_LABELS[shortlistEntry.status]}</div>
              </div>
            </div>
            <div className="label" style={{ marginBottom: 4 }}>
              Note
            </div>
            <div style={{ fontSize: 13, color: "var(--color-text-secondary)", whiteSpace: "pre-wrap" }}>
              {shortlistEntry.note.trim() ? shortlistEntry.note : "No scout notes added."}
            </div>
          </>
        ) : (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-3)" }}>
            <span style={{ fontSize: 13, color: "var(--color-text-tertiary)" }}>No scout notes added.</span>
            <button
              className="no-print"
              onClick={() => addToShortlist(identity.playerName, active.competitionId, active.seasonId)}
              style={btnSecondary}
            >
              Add to shortlist
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function evidenceMark(status: MatchEvaluation["status"]): string {
  if (status === "matched") return "✓";
  if (status === "unmet") return "✗";
  return "?";
}

function evidenceColor(status: MatchEvaluation["status"]): string {
  if (status === "matched") return "var(--color-accent-text)";
  if (status === "unmet") return "var(--color-warning)";
  return "var(--color-text-tertiary)";
}

function evidenceValue(e: MatchEvaluation): string {
  if (e.status === "insufficient_data") return "Insufficient data";
  const value = e.value != null ? e.value.toFixed(1) : "N/A";
  const range = [
    e.minimum != null ? `min ${e.minimum}` : null,
    e.maximum != null ? `max ${e.maximum}` : null,
  ]
    .filter(Boolean)
    .join(", ");
  return range ? `${value} (${range})` : value;
}

// Perguntas geradas por template determinístico a partir dos próprios
// dados da avaliação -- nunca prosa gerada por IA. Cada frase é
// diretamente rastreável ao valor/threshold devolvido pelo backend.
function questionFor(e: MatchEvaluation): string {
  if (e.status === "insufficient_data") {
    return `${e.label}: no data available for this player in this context — worth investigating directly.`;
  }
  const value = e.value != null ? e.value.toFixed(1) : "N/A";
  if (e.minimum != null && (e.value == null || e.value < e.minimum)) {
    return `${e.label}: ${value} falls below the target minimum of ${e.minimum} — does this reflect the player's true profile, or sample-specific variance?`;
  }
  if (e.maximum != null && (e.value == null || e.value > e.maximum)) {
    return `${e.label}: ${value} exceeds the target maximum of ${e.maximum} — worth confirming with additional footage.`;
  }
  return `${e.label}: ${value} is outside the target range — worth reviewing.`;
}

const btnSecondary = {
  padding: "9px 16px",
  fontSize: 13,
  fontWeight: 700,
  borderRadius: "var(--radius-sm)",
  cursor: "pointer",
  border: "1px solid var(--color-border)",
  background: "transparent",
  color: "var(--color-text-secondary)",
} as const;
