import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getComparison } from "../api/client";
import type { PerformanceRow } from "../api/types";
import { ContextBadge } from "../components/ContextBadge";
import { BackLink } from "../components/BackLink";
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

const COLORS = ["#22936b", "#c98a3f", "#4f7cc9", "#a464c9"];

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

interface MetricSpec {
  label: string;
  get: (r: PerformanceRow) => number | null;
  fmt: (v: number | null) => string;
}

const GROUPS: { title: string; note?: string; metrics: MetricSpec[] }[] = [
  {
    title: "Shot Stopping",
    metrics: [
      { label: "Save %", get: (r) => r.metrics.shotStopping.savePct, fmt: (v) => formatPct(v) },
      { label: "Shots faced", get: (r) => r.metrics.shotStopping.shotsFaced, fmt: (v) => formatCount(v) },
      { label: "Shots saved", get: (r) => r.metrics.shotStopping.shotsSaved, fmt: (v) => formatCount(v) },
      { label: "Goals conceded", get: (r) => r.metrics.shotStopping.goalsConceded, fmt: (v) => formatCount(v) },
    ],
  },
  {
    title: "Sweeping",
    note: "Absence of actions is not the same as zero.",
    metrics: [
      { label: "Actions", get: (r) => r.metrics.sweeping.sweeperActions, fmt: (v) => formatCount(v, NO_ACTIONS_LABEL) },
      { label: "Actions /90", get: (r) => r.metrics.sweeping.sweeperActionsP90, fmt: (v) => formatRateP90(v, NO_ACTIONS_LABEL) },
      { label: "Avg. distance", get: (r) => r.metrics.sweeping.avgDistanceFromGoal, fmt: (v) => formatDistance(v, NO_ACTIONS_LABEL) },
    ],
  },
  {
    title: "Distribution",
    metrics: [
      { label: "Pass success", get: (r) => r.metrics.distribution.passSuccessPct, fmt: (v) => formatPct(v) },
      { label: "Avg. pass length", get: (r) => r.metrics.distribution.avgPassLength, fmt: (v) => formatDistance(v) },
      { label: "Long ball %", get: (r) => r.metrics.distribution.longBallPct, fmt: (v) => formatPct(v) },
    ],
  },
  {
    title: "Market",
    metrics: [
      { label: "Market value", get: (r) => r.marketValueEur, fmt: (v) => formatMarketValue(v) },
      { label: "Minutes", get: (r) => r.minutes, fmt: (v) => formatCount(v) },
    ],
  },
];

export function Compare() {
  const [params] = useSearchParams();
  const [players, setPlayers] = useState<PerformanceRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = params.get("players");
    if (!raw) {
      setError("No players selected. Go to Discover and select 2–4 goalkeepers.");
      setLoading(false);
      return;
    }
    const selections = raw.split(",").map((chunk) => {
      const [playerName, competitionId, seasonId] = chunk.split(":");
      return { playerName, competitionId: Number(competitionId), seasonId: Number(seasonId) };
    });
    setLoading(true);
    getComparison(selections)
      .then((res) => setPlayers(res.players))
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [params]);

  if (loading) return <LoadingState label="Loading comparison…" />;
  if (error) return <ErrorState message={error} />;
  if (!players) return null;

  return (
    <div>
      <BackLink label="Back to Discover" to="/discover" />
      <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 4px" }}>Compare</h1>
      <p style={{ color: "var(--color-text-secondary)", margin: "0 0 var(--space-6)" }}>
        {players.length} goalkeepers, each in their own competition/season context. To change who's
        being compared, go back to Discover and select again.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${players.length}, 1fr)`,
          gap: "var(--space-4)",
          marginBottom: "var(--space-6)",
        }}
      >
        {players.map((p, i) => (
          <div key={p.playerName} className="card">
            <div style={{ width: 8, height: 8, borderRadius: 4, background: COLORS[i], marginBottom: 8 }} />
            <div style={{ fontWeight: 700, fontSize: 15 }}>{p.playerName}</div>
            <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 8 }}>
              {p.club ?? "Club unknown"}
            </div>
            <ContextBadge competitionId={p.competitionId} seasonId={p.seasonId} minutes={p.minutes} />
          </div>
        ))}
      </div>

      <div style={{ marginBottom: "var(--space-6)" }}>
        <RadarChart
          labels={RADAR_LABELS}
          series={players.map((p, i) => ({ name: p.playerName, color: COLORS[i], values: radarValues(p) }))}
        />
      </div>

      {GROUPS.map((group) => (
        <section key={group.title} style={{ marginBottom: "var(--space-6)" }}>
          <div className="section-title">{group.title}</div>
          {group.note && (
            <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginBottom: 8 }}>{group.note}</div>
          )}
          <div className="scroll-x">
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr>
                  <th style={thStyle}></th>
                  {players.map((p) => (
                    <th key={p.playerName} style={thStyle}>
                      {p.playerName}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {group.metrics.map((metric) => (
                  <tr key={metric.label}>
                    <td style={tdLabelStyle}>{metric.label}</td>
                    {players.map((p) => (
                      <td key={p.playerName} className="tabular" style={tdStyle}>
                        {metric.fmt(metric.get(p))}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}

const thStyle: CSSProperties = {
  textAlign: "left",
  padding: "8px 12px",
  borderBottom: "1px solid var(--color-border)",
  color: "var(--color-text-secondary)",
  fontWeight: 600,
};

const tdStyle: CSSProperties = {
  padding: "8px 12px",
  borderBottom: "1px solid var(--color-border-soft)",
  fontWeight: 600,
};

const tdLabelStyle: CSSProperties = {
  ...tdStyle,
  color: "var(--color-text-secondary)",
  fontWeight: 500,
};
