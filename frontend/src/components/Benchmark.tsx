import type { BenchmarkMetric, BenchmarkResponse } from "../api/types";
import { formatDistance, formatPct, formatRateP90 } from "../lib/format";
import { EmptyState, LoadingState } from "./States";

// O mesmo `benchmark.totalPeerCount`/`available` que já vem do backend --
// "cobertura" não é um julgamento de performance, é só quantos pares
// comparáveis existem de facto. Nunca inventa um número.
function CoverageLine({ benchmark }: { benchmark: BenchmarkResponse }) {
  const limited = !benchmark.available;
  return (
    <div style={{ marginBottom: "var(--space-3)" }}>
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          color: limited ? "var(--color-warning)" : "var(--color-text-tertiary)",
        }}
      >
        {limited ? "Limited coverage" : "Data coverage"}
      </div>
      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 2 }}>
        {benchmark.competitionName} · {benchmark.seasonName} — {benchmark.totalPeerCount}{" "}
        {benchmark.totalPeerCount === 1 ? "comparable goalkeeper" : "comparable goalkeepers"} · ≥
        {benchmark.minimumMinutes.toFixed(0)} min
      </div>
    </div>
  );
}

// Cada métrica de benchmark usa o mesmo formatador já usado nas secções
// de métricas do Player Profile -- não é uma formatação nova, só
// reaplicada aqui.
const VALUE_FORMATTERS: Record<string, (v: number | null) => string> = {
  save_pct: (v) => formatPct(v),
  sweeper_actions_p90: (v) => formatRateP90(v),
  avg_distance_from_goal: (v) => formatDistance(v),
  pass_success_pct: (v) => formatPct(v),
  long_ball_pct: (v) => formatPct(v),
};

function ordinal(n: number): string {
  const rounded = Math.round(n);
  const mod100 = rounded % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${rounded}th`;
  switch (rounded % 10) {
    case 1:
      return `${rounded}st`;
    case 2:
      return `${rounded}nd`;
    case 3:
      return `${rounded}rd`;
    default:
      return `${rounded}th`;
  }
}

function BenchmarkItem({ metric }: { metric: BenchmarkMetric }) {
  const format = VALUE_FORMATTERS[metric.key] ?? ((v: number | null) => (v != null ? `${v}` : "N/A"));
  const value = format(metric.value);

  let percentileText: string;
  let showBar = false;
  let caveat: string | null = null;

  if (metric.status === "no_data") {
    percentileText = "No data for this metric in this sample.";
  } else if (metric.status === "insufficient") {
    percentileText = "Insufficient comparison sample";
  } else {
    percentileText = `${ordinal(metric.percentile ?? 0)} percentile`;
    showBar = true;
    if (metric.status === "small") caveat = "Small comparison sample";
  }

  return (
    <div
      style={{
        background: "var(--color-surface-raised)",
        border: "1px solid var(--color-border-soft)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-3) var(--space-4)",
      }}
    >
      <div className="label">{metric.label}</div>
      <div className="tabular" style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 6 }}>{percentileText}</div>
      {showBar && (
        <div
          style={{
            height: 6,
            borderRadius: 999,
            background: "var(--color-border-soft)",
            marginTop: 6,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${Math.max(0, Math.min(100, metric.percentile ?? 0))}%`,
              background: "var(--color-accent)",
              borderRadius: 999,
            }}
          />
        </div>
      )}
      <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 8 }}>
        {metric.status !== "no_data" && (
          <>
            {metric.peerCount} {metric.peerCount === 1 ? "goalkeeper" : "goalkeepers"}
            {caveat && (
              <>
                {" · "}
                <span style={{ color: "var(--color-warning)", fontWeight: 600 }}>{caveat}</span>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export function BenchmarkSection({
  benchmark,
  loading,
  error,
}: {
  benchmark: BenchmarkResponse | null;
  loading: boolean;
  error: string | null;
}) {
  return (
    <div style={{ marginBottom: "var(--space-6)" }}>
      <div className="section-title">Performance benchmark</div>

      {loading && <LoadingState label="Loading benchmark…" />}

      {!loading && error && <EmptyState message="Benchmark unavailable for this sample." />}

      {!loading && !error && benchmark && (
        <>
          <CoverageLine benchmark={benchmark} />

          {!benchmark.available && (
            <div style={{ fontSize: 12, color: "var(--color-text-tertiary)" }}>
              Not enough comparable goalkeepers are available in this competition/season.
            </div>
          )}

          {benchmark.available && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "var(--space-3)",
              }}
            >
              {benchmark.metrics.map((metric) => (
                <BenchmarkItem key={metric.key} metric={metric} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
