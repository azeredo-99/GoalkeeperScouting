import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getPlayerProfile } from "../api/client";
import type { PerformanceRow, PlayerProfileResponse } from "../api/types";
import { ContextBadge, SampleIndicator } from "../components/ContextBadge";
import { BackLink } from "../components/BackLink";
import { MetricCard, MetricGroup } from "../components/MetricGroup";
import { RadarChart } from "../components/RadarChart";
import { ErrorState, LoadingState } from "../components/States";
import {
  NO_ACTIONS_LABEL,
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
  const [data, setData] = useState<PlayerProfileResponse | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
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
  }, [player]);

  const active = useMemo(() => data?.performances[selectedIndex] ?? null, [data, selectedIndex]);

  if (loading) return <LoadingState label="Loading player…" />;
  if (error) return <ErrorState message={error} />;
  if (!data || !active) return null;

  const { identity } = data;
  const hasMultipleContexts = data.performances.length > 1;

  return (
    <div>
      <BackLink label="Back to Discover" to="/discover" />
      {/* PLAYER HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-2)" }}>
        <div>
          <h1 style={{ fontSize: 30, fontWeight: 800, margin: 0 }}>{identity.playerName}</h1>
          <div style={{ color: "var(--color-text-secondary)", fontSize: 14, marginTop: 4 }}>
            Goalkeeper · {identity.club ?? "Club unknown"}
            {identity.age != null ? ` · ${identity.age} years` : ""}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="label">Market value</div>
          <div style={{ fontSize: 22, fontWeight: 800 }} className="tabular">
            {formatMarketValue(identity.marketValueEur)}
          </div>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>
            Peak {formatMarketValue(identity.highestMarketValueEur)}
          </div>
        </div>
      </div>
      <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: "var(--space-5)" }}>
        Age and market value reflect the player's current status — not the season below.
      </div>

      {/* CONTEXT */}
      <div className="card" style={{ marginBottom: "var(--space-6)" }}>
        <div className="section-title">Sample context</div>
        {hasMultipleContexts && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: "var(--space-3)" }}>
            {data.performances.map((p, i) => (
              <button
                key={`${p.competitionId}-${p.seasonId}`}
                onClick={() => setSelectedIndex(i)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 999,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                  border: i === selectedIndex ? "1px solid var(--color-accent)" : "1px solid var(--color-border)",
                  background: i === selectedIndex ? "var(--color-accent-soft)" : "transparent",
                  color: i === selectedIndex ? "var(--color-accent-text)" : "var(--color-text-secondary)",
                }}
              >
                #{p.competitionId} / #{p.seasonId}
              </button>
            ))}
          </div>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
          <ContextBadge competitionId={active.competitionId} seasonId={active.seasonId} minutes={active.minutes} />
          <SampleIndicator minutes={active.minutes} />
        </div>
        {hasMultipleContexts && (
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 8 }}>
            This goalkeeper has performance in more than one competition/season. Metrics below always
            reflect the selected context only — never combined.
          </div>
        )}
      </div>

      {/* METRICS */}
      <MetricGroup title="Shot Stopping">
        <MetricCard label="Save %" value={formatPct(active.metrics.shotStopping.savePct)} />
        <MetricCard label="Shots faced" value={formatCount(active.metrics.shotStopping.shotsFaced)} />
        <MetricCard label="Shots saved" value={formatCount(active.metrics.shotStopping.shotsSaved)} />
        <MetricCard label="Goals conceded" value={formatCount(active.metrics.shotStopping.goalsConceded)} />
        <MetricCard label="Shots faced /90" value={formatRateP90(active.metrics.shotStopping.shotsFacedP90)} />
      </MetricGroup>

      <MetricGroup title="Sweeping" note="Absence of actions is not the same as zero.">
        <MetricCard label="Actions" value={formatCount(active.metrics.sweeping.sweeperActions, NO_ACTIONS_LABEL)} />
        <MetricCard label="Actions /90" value={formatRateP90(active.metrics.sweeping.sweeperActionsP90, NO_ACTIONS_LABEL)} />
        <MetricCard label="Avg. distance" value={formatDistance(active.metrics.sweeping.avgDistanceFromGoal, NO_ACTIONS_LABEL)} />
        <MetricCard label="Max distance" value={formatDistance(active.metrics.sweeping.maxDistanceFromGoal, NO_ACTIONS_LABEL)} />
      </MetricGroup>

      <MetricGroup title="Distribution">
        <MetricCard label="Pass success" value={formatPct(active.metrics.distribution.passSuccessPct)} />
        <MetricCard label="Total passes" value={formatCount(active.metrics.distribution.totalPasses)} />
        <MetricCard label="Avg. pass length" value={formatDistance(active.metrics.distribution.avgPassLength)} />
        <MetricCard label="Long ball %" value={formatPct(active.metrics.distribution.longBallPct)} />
      </MetricGroup>

      {/* VISUALIZATIONS */}
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "var(--space-6)", marginBottom: "var(--space-6)" }}>
        <div>
          <div className="section-title">Performance radar</div>
          <RadarChart
            labels={RADAR_LABELS}
            series={[{ name: identity.playerName, color: "#22936b", values: radarValues(active) }]}
          />
        </div>
        <div>
          <div className="section-title">Sweeper map</div>
          <div
            style={{
              height: 180,
              borderRadius: "var(--radius-md)",
              border: "1px dashed var(--color-border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--color-text-tertiary)",
              fontSize: 13,
              textAlign: "center",
              padding: "var(--space-4)",
            }}
          >
            Shot/location data unavailable for this sample.
          </div>
        </div>
      </div>

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
  );
}
