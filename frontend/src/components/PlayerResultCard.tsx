import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import type { PerformanceRow } from "../api/types";
import { formatMarketValue, formatPct } from "../lib/format";
import { ContextBadge } from "./ContextBadge";

export function PlayerResultCard({
  row,
  onToggleCompare,
  selectedForCompare,
}: {
  row: PerformanceRow;
  onToggleCompare?: (row: PerformanceRow) => void;
  selectedForCompare?: boolean;
}) {
  const navigate = useNavigate();

  return (
    <div
      className="card"
      style={{
        padding: "var(--space-4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "var(--space-4)",
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ fontSize: 15, fontWeight: 700 }}>{row.playerName}</span>
          <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
            {row.club ?? "Club unknown"}
          </span>
        </div>
        <div style={{ marginTop: 6 }}>
          <ContextBadge competitionId={row.competitionId} seasonId={row.seasonId} minutes={row.minutes} />
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-5)", flexShrink: 0 }}>
        <div style={{ textAlign: "right" }}>
          <div className="label">Market value</div>
          <div className="tabular" style={{ fontWeight: 700 }}>
            {formatMarketValue(row.marketValueEur)}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="label">Save %</div>
          <div className="tabular" style={{ fontWeight: 700 }}>
            {formatPct(row.metrics.shotStopping.savePct)}
          </div>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => navigate(`/player/${encodeURIComponent(row.playerName)}`)}
            style={btnPrimary}
          >
            View profile
          </button>
          {onToggleCompare && (
            <button
              onClick={() => onToggleCompare(row)}
              style={selectedForCompare ? btnSecondaryActive : btnSecondary}
            >
              {selectedForCompare ? "Selected" : "Compare"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

const btnBase: CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  borderRadius: "var(--radius-sm)",
  padding: "8px 12px",
  cursor: "pointer",
  border: "1px solid var(--color-border)",
  background: "transparent",
  color: "var(--color-text-secondary)",
  whiteSpace: "nowrap",
};

const btnPrimary: CSSProperties = {
  ...btnBase,
  background: "var(--color-accent)",
  borderColor: "var(--color-accent)",
  color: "#04150e",
};

const btnSecondary: CSSProperties = { ...btnBase };

const btnSecondaryActive: CSSProperties = {
  ...btnBase,
  borderColor: "var(--color-accent)",
  color: "var(--color-accent-text)",
  background: "var(--color-accent-soft)",
};
