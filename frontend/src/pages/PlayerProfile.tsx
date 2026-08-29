import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getPlayerBenchmark, getPlayerProfile, getSimilarity } from "../api/client";
import type { BenchmarkResponse, PerformanceRow, PlayerProfileResponse, SimilarityResponse } from "../api/types";
import { SampleIndicator } from "../components/ContextBadge";
import { addToShortlist, removeFromShortlist, useIsShortlisted } from "../lib/shortlist";
import { buildTakeaways } from "../lib/takeaways";
import type { CSSProperties, ReactNode } from "react";
import { BackLink } from "../components/BackLink";
import { BenchmarkSection } from "../components/Benchmark";
import { DimensionSnapshot } from "../components/DimensionSnapshot";
import { MetricCard, MetricGroup } from "../components/MetricGroup";
import { RadarChart } from "../components/RadarChart";
import { SweeperMap } from "../components/SweeperMap";
import { ErrorState, LoadingState } from "../components/States";
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

export function PlayerProfile() {
  const { player } = useParams<{ player: string }>();
  const navigate = useNavigate();
  // Perfil ativo em Discover, só a atravessar esta página até ao
  // Scouting Report -- nunca lido nem usado aqui, ver nota em
  // goToReport().
  const [searchParams] = useSearchParams();
  const scoutingProfileId = searchParams.get("scouting_profile");
  const [data, setData] = useState<PlayerProfileResponse | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!player) return;
    setLoading(true);
    setError(null);
    getPlayerProfile(player)
      .then((res) => {
        setData(res);
        setSelectedIndex(0);
      })
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [player]);

  const active = useMemo(() => data?.performances[selectedIndex] ?? null, [data, selectedIndex]);

  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkError, setBenchmarkError] = useState<string | null>(null);

  useEffect(() => {
    if (!active) return;
    setBenchmark(null);
    setBenchmarkError(null);
    setBenchmarkLoading(true);
    getPlayerBenchmark(active.playerName, active.competitionId, active.seasonId)
      .then(setBenchmark)
      .catch((e) => setBenchmarkError((e as Error).message))
      .finally(() => setBenchmarkLoading(false));
  }, [active?.playerName, active?.competitionId, active?.seasonId]);

  // Preview de Similarity -- independente do contexto selecionado no
  // Profile: o algoritmo já opera sempre sobre a linha canónica do
  // jogador (mais minutos), nunca sobre a amostra que o scout está a
  // ver aqui (ver similarity_engine/`table`). Por isso o pedido só
  // depende do jogador, não de `active`, e nunca é refeito ao trocar
  // de contexto -- resultado idêntico, pedido desperdiçado evitado.
  const [similarPreview, setSimilarPreview] = useState<SimilarityResponse | null>(null);
  const [similarLoading, setSimilarLoading] = useState(false);

  useEffect(() => {
    if (!player) return;
    setSimilarPreview(null);
    setSimilarLoading(true);
    getSimilarity(player, { shotStopping: 30, distribution: 35, proactivity: 35 }, 3)
      .then(setSimilarPreview)
      .catch(() => setSimilarPreview(null))
      .finally(() => setSimilarLoading(false));
  }, [player]);

  const shortlisted = useIsShortlisted(player ?? "");

  if (loading) return <LoadingState label="Loading player…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data || !active) return null;

  const { identity } = data;
  const hasMultipleContexts = data.performances.length > 1;

  function toggleShortlist() {
    if (shortlisted) {
      removeFromShortlist(identity.playerName);
    } else {
      addToShortlist(identity.playerName, active!.competitionId, active!.seasonId);
    }
  }

  function goToCompare() {
    const q = `${identity.playerName}:${active!.competitionId}:${active!.seasonId}`;
    navigate(`/compare?players=${encodeURIComponent(q)}`);
  }

  const takeaways = buildTakeaways(active, data.performances.length, benchmark);

  function goToReport() {
    const params = new URLSearchParams({
      competition_id: String(active!.competitionId),
      season_id: String(active!.seasonId),
    });
    if (scoutingProfileId) params.set("scouting_profile", scoutingProfileId);
    navigate(`/report/${encodeURIComponent(identity.playerName)}?${params.toString()}`);
  }

  return (
    <div>
      <BackLink label="Back to Discover" to="/discover" />
      {/* PLAYER HEADER */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "var(--space-4)",
          flexWrap: "wrap",
          marginBottom: "var(--space-5)",
        }}
      >
        <div>
          <h1 style={{ fontSize: 30, fontWeight: 800, margin: "0 0 4px" }}>{identity.playerName}</h1>
          <div style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>Goalkeeper</div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={goToCompare} style={headerBtnSecondary}>
            Compare
          </button>
          <button
            onClick={toggleShortlist}
            style={{
              padding: "9px 16px",
              fontSize: 13,
              fontWeight: 700,
              borderRadius: "var(--radius-sm)",
              cursor: "pointer",
              border: shortlisted ? "1px solid var(--color-accent)" : "1px solid var(--color-border)",
              background: shortlisted ? "var(--color-accent-soft)" : "transparent",
              color: shortlisted ? "var(--color-accent-text)" : "var(--color-text-secondary)",
            }}
          >
            {shortlisted ? "Remove from shortlist" : "Add to shortlist"}
          </button>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--space-4)",
          marginBottom: "var(--space-6)",
        }}
      >
        {/* CURRENT PLAYER INFORMATION */}
        <div className="card">
          <div className="section-title">Current player information</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "var(--space-3)" }}>
            <div>
              <div className="label">Position</div>
              <div style={{ fontSize: 16, fontWeight: 700 }}>Goalkeeper</div>
            </div>
            <div>
              <div className="label">Age (this season)</div>
              <div className="tabular" style={{ fontSize: 16, fontWeight: 700 }}>
                {active.age != null ? `${active.age}` : "N/A"}
              </div>
            </div>
            <div>
              <div className="label">Club</div>
              <div style={{ fontSize: 16, fontWeight: 700 }}>{formatClub(identity.club)}</div>
            </div>
            <div>
              <div className="label">Current market value</div>
              <div className="tabular" style={{ fontSize: 16, fontWeight: 700 }}>
                {formatMarketValue(identity.marketValueEur)}
              </div>
            </div>
            <div>
              <div className="label">Peak market value</div>
              <div className="tabular" style={{ fontSize: 16, fontWeight: 700 }}>
                {formatMarketValue(identity.highestMarketValueEur)}
              </div>
            </div>
          </div>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: "var(--space-3)" }}>
            Reflects the player's current status, independent of the performance sample below.
          </div>
        </div>

        {/* PERFORMANCE SAMPLE */}
        <div className="card">
          <div className="section-title">Performance sample</div>
          {hasMultipleContexts && (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)", marginBottom: "var(--space-3)" }}>
              <Field label="Competition">
                <select
                  value={selectedIndex}
                  onChange={(e) => setSelectedIndex(Number(e.target.value))}
                  style={selectStyle}
                >
                  {data.performances.map((p, i) => (
                    <option key={`${p.competitionId}-${p.seasonId}`} value={i}>
                      {p.competitionName} — {p.seasonName}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
          )}
          <div style={{ fontSize: 18, fontWeight: 700 }}>{active.competitionName}</div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: "var(--space-3)" }}>
            {active.seasonName}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
            <div>
              <div className="label">Minutes</div>
              <div className="tabular" style={{ fontSize: 16, fontWeight: 700 }}>
                {active.minutes != null ? active.minutes.toFixed(0) : "N/A"}
              </div>
            </div>
            <SampleIndicator minutes={active.minutes} />
          </div>
          {hasMultipleContexts && (
            <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: "var(--space-3)" }}>
              This goalkeeper has performance in more than one competition/season. Metrics below always
              reflect the selected sample only — never combined.
            </div>
          )}
        </div>
      </div>

      {/* SCOUTING SNAPSHOT -- compact, no scores, just the headline real
          metric from each of the three existing performance dimensions */}
      <div className="card" style={{ marginBottom: "var(--space-4)" }}>
        <div className="section-title">Scouting snapshot</div>
        <DimensionSnapshot metrics={active.metrics} />
      </div>

      {/* TAKEAWAYS -- deterministic sentences describing evidence, never a
          football judgement. Placed right after the snapshot, before the
          detailed numbers, so the page reads narrative-first. */}
      <div style={{ marginBottom: "var(--space-6)" }}>
        <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 4 }}>
          {takeaways.map((t) => (
            <li key={t} style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
              — {t}
            </li>
          ))}
        </ul>
      </div>

      {/* METRICS -- the underlying evidence for the snapshot above */}
      <MetricGroup title="Shot Stopping">
        <MetricCard
          label="Save %"
          value={formatPct(active.metrics.shotStopping.savePct)}
          hint="Percentage of shots on target saved in this sample."
        />
        <MetricCard
          label="Shots faced"
          value={formatCount(active.metrics.shotStopping.shotsFaced)}
          hint="Total shots faced, on target or not."
        />
        <MetricCard
          label="Shots saved"
          value={formatCount(active.metrics.shotStopping.shotsSaved)}
          hint="Shots stopped by the goalkeeper."
        />
        <MetricCard
          label="Goals conceded"
          value={formatCount(active.metrics.shotStopping.goalsConceded)}
          hint="Goals conceded from shots faced."
        />
        <MetricCard
          label="Shots faced /90"
          value={formatRateP90(active.metrics.shotStopping.shotsFacedP90)}
          hint="Shots faced, normalised to a 90-minute rate."
        />
      </MetricGroup>

      <MetricGroup title="Sweeping" note="Absence of actions is not the same as zero.">
        <MetricCard
          label="Actions"
          value={formatCount(active.metrics.sweeping.sweeperActions, NO_ACTIONS_LABEL)}
          hint="Actions taken outside the box as a sweeper-keeper."
        />
        <MetricCard
          label="Actions /90"
          value={formatRateP90(active.metrics.sweeping.sweeperActionsP90, NO_ACTIONS_LABEL)}
          hint="Sweeper actions, normalised to a 90-minute rate."
        />
        <MetricCard
          label="Avg. distance"
          value={formatDistance(active.metrics.sweeping.avgDistanceFromGoal, NO_ACTIONS_LABEL)}
          hint="Average distance from goal for sweeper actions."
        />
        <MetricCard
          label="Max distance"
          value={formatDistance(active.metrics.sweeping.maxDistanceFromGoal, NO_ACTIONS_LABEL)}
          hint="Furthest sweeper action from goal in this sample."
        />
      </MetricGroup>

      <MetricGroup title="Distribution">
        <MetricCard
          label="Pass success"
          value={formatPct(active.metrics.distribution.passSuccessPct)}
          hint="Percentage of passes completed successfully."
        />
        <MetricCard
          label="Total passes"
          value={formatCount(active.metrics.distribution.totalPasses)}
          hint="Total passes attempted."
        />
        <MetricCard
          label="Avg. pass length"
          value={formatDistance(active.metrics.distribution.avgPassLength)}
          hint="Average distance of each pass."
        />
        <MetricCard
          label="Long ball %"
          value={formatPct(active.metrics.distribution.longBallPct)}
          hint="Percentage of passes longer than 40 metres."
        />
      </MetricGroup>

      <BenchmarkSection benchmark={benchmark} loading={benchmarkLoading} error={benchmarkError} />

      {/* VISUAL PROFILE -- secondary, never the hero of the page */}
      <div className="section-title">Visual profile</div>
      <div style={{ display: "flex", gap: "var(--space-6)", flexWrap: "wrap", marginBottom: "var(--space-6)" }}>
        <div style={{ flex: "0 0 auto" }}>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8 }}>Performance radar</div>
          <RadarChart
            labels={RADAR_LABELS}
            series={[{ name: identity.playerName, color: "#22936b", values: radarValues(active) }]}
            emptyMessage="Not enough recorded metrics for a radar in this sample."
            size={220}
          />
        </div>
        <div style={{ flex: "1 1 260px", maxWidth: 340 }}>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8 }}>Sweeper map</div>
          <SweeperMap height={220} />
        </div>
      </div>

      {/* SIMILAR GOALKEEPERS -- lightweight preview, one request per
          player (not per context switch, see effect above). Reuses the
          existing algorithm output exactly as returned; no recomputation. */}
      {similarLoading && (
        <div style={{ marginBottom: "var(--space-6)" }}>
          <div className="section-title">Similar goalkeepers</div>
          <LoadingState label="Loading similar goalkeepers…" />
        </div>
      )}
      {!similarLoading && similarPreview && similarPreview.results.length > 0 && (
        <div style={{ marginBottom: "var(--space-6)" }}>
          <div className="section-title">Similar goalkeepers</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
            {similarPreview.results.slice(0, 3).map((r) => (
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
          <button onClick={() => navigate(`/similar/${encodeURIComponent(identity.playerName)}`)} style={headerBtnSecondary}>
            View all similar goalkeepers
          </button>
        </div>
      )}

      {/* SCOUT DECISION AREA -- the product shows evidence; the scout
          decides. No automatic recommendation. */}
      <div className="card" style={{ padding: "var(--space-5)" }}>
        <div className="section-title">Shortlist</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            onClick={toggleShortlist}
            style={{
              padding: "12px 20px",
              fontSize: 13,
              fontWeight: 700,
              borderRadius: "var(--radius-sm)",
              cursor: "pointer",
              border: shortlisted ? "1px solid var(--color-accent)" : "1px solid var(--color-border)",
              background: shortlisted ? "var(--color-accent-soft)" : "transparent",
              color: shortlisted ? "var(--color-accent-text)" : "var(--color-text-secondary)",
            }}
          >
            {shortlisted ? "Remove from shortlist" : "Add to shortlist"}
          </button>
          <button onClick={goToCompare} style={headerBtnSecondary}>
            Compare
          </button>
          <button onClick={goToReport} style={headerBtnSecondary}>
            Scouting report
          </button>
          <button
            onClick={() => navigate(`/similar/${encodeURIComponent(identity.playerName)}`)}
            style={{
              padding: "12px 20px",
              fontSize: 13,
              fontWeight: 700,
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--color-accent)",
              background: "var(--color-accent)",
              color: "#04150e",
              cursor: "pointer",
            }}
          >
            Find similar goalkeepers
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <div className="label" style={{ marginBottom: 4 }}>
        {label}
      </div>
      {children}
    </div>
  );
}

const headerBtnSecondary: CSSProperties = {
  padding: "9px 16px",
  fontSize: 13,
  fontWeight: 700,
  borderRadius: "var(--radius-sm)",
  cursor: "pointer",
  border: "1px solid var(--color-border)",
  background: "transparent",
  color: "var(--color-text-secondary)",
};

const selectStyle: CSSProperties = {
  padding: "8px 10px",
  fontSize: 13,
  fontWeight: 600,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
  width: "100%",
};
