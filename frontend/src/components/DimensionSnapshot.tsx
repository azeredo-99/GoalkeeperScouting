import type { PerformanceMetrics } from "../api/types";
import { NO_ACTIONS_LABEL, formatDistance, formatPct, formatRateP90 } from "../lib/format";

// As mesmas três dimensões usadas em todo o produto (Player Profile,
// Similarity) -- nunca um score novo, só os valores reais já calculados
// agrupados por categoria. Usado como "scouting snapshot" (bloco
// completo, um por jogador de referência) ou como tira compacta (lista
// de candidatos), mas a mesma fonte de dados e a mesma leitura em
// ambos os casos.
export function DimensionSnapshot({ metrics }: { metrics: PerformanceMetrics }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
        gap: "var(--space-4)",
      }}
    >
      <DimensionColumn
        title="Shot Stopping"
        primary={formatPct(metrics.shotStopping.savePct)}
        primaryLabel="Save %"
        secondary={`${formatRateP90(metrics.shotStopping.shotsFacedP90)} shots faced /90`}
      />
      <DimensionColumn
        title="Sweeping"
        primary={formatRateP90(metrics.sweeping.sweeperActionsP90, NO_ACTIONS_LABEL)}
        primaryLabel="Actions /90"
        secondary={
          metrics.sweeping.avgDistanceFromGoal != null
            ? `${formatDistance(metrics.sweeping.avgDistanceFromGoal)} avg. distance`
            : NO_ACTIONS_LABEL
        }
      />
      <DimensionColumn
        title="Distribution"
        primary={formatPct(metrics.distribution.passSuccessPct)}
        primaryLabel="Pass success"
        secondary={`${formatPct(metrics.distribution.longBallPct)} long balls`}
      />
    </div>
  );
}

function DimensionColumn({
  title,
  primary,
  primaryLabel,
  secondary,
}: {
  title: string;
  primary: string;
  primaryLabel: string;
  secondary: string;
}) {
  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>
        {title}
      </div>
      <div className="tabular" style={{ fontSize: 24, fontWeight: 800 }}>
        {primary}
      </div>
      <div style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>{primaryLabel}</div>
      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 6 }}>{secondary}</div>
    </div>
  );
}

// Variante compacta para linhas de resultado (Similarity) -- os mesmos
// valores brutos que alimentam o algoritmo, sem sub-score nem cor de
// "bom/mau": o scout lê os números, não uma nota.
export function DimensionInline({ metrics }: { metrics: PerformanceMetrics }) {
  return (
    <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", fontSize: 12 }}>
      <InlineStat label="Save %" value={formatPct(metrics.shotStopping.savePct)} />
      <InlineStat
        label="Sweeper /90"
        value={formatRateP90(metrics.sweeping.sweeperActionsP90, NO_ACTIONS_LABEL)}
      />
      <InlineStat label="Pass %" value={formatPct(metrics.distribution.passSuccessPct)} />
      <InlineStat label="Long ball %" value={formatPct(metrics.distribution.longBallPct)} />
    </div>
  );
}

function InlineStat({ label, value }: { label: string; value: string }) {
  return (
    <span style={{ color: "var(--color-text-secondary)" }}>
      {label} <span className="tabular" style={{ color: "var(--color-text)", fontWeight: 700 }}>{value}</span>
    </span>
  );
}
