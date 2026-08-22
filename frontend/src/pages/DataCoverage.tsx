import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { getDataCoverage } from "../api/client";
import type { CoverageStatus, DataCoverageResponse } from "../api/types";
import { ErrorState, LoadingState } from "../components/States";

const STATUS_LABEL: Record<CoverageStatus, string> = {
  strong: "Strong coverage",
  partial: "Partial coverage",
  limited: "Limited coverage",
  insufficient: "Insufficient data",
};

const STATUS_COLOR: Record<CoverageStatus, string> = {
  strong: "var(--color-accent-text)",
  partial: "var(--color-text-secondary)",
  limited: "var(--color-warning)",
  insufficient: "var(--color-danger)",
};

// Vista interna -- não é uma página de marketing. Mostra exatamente o
// que a base de dados contém, para que a equipa saiba onde o produto
// já é fiável e onde ainda não é. Números reais só, sem "coverage
// score" inventado.
export function DataCoverage() {
  const [data, setData] = useState<DataCoverageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    getDataCoverage()
      .then(setData)
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  return (
    <div>
      <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 4px" }}>Data Coverage</h1>
      <p style={{ color: "var(--color-text-secondary)", margin: "0 0 var(--space-6)" }}>
        Internal view of what the system currently knows, per competition/season. Not a performance judgement.
      </p>

      {loading && <LoadingState label="Loading coverage…" />}
      {error && <ErrorState message={error} onRetry={load} />}

      {!loading && !error && data && (
        <>
          <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginBottom: "var(--space-4)" }}>
            Benchmarkable = goalkeepers with ≥{data.minimumMinutes.toFixed(0)} minutes in that context (the same
            threshold used by Performance Benchmark).
          </div>
          <div className="scroll-x">
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr>
                  <th style={thStyle}>Competition</th>
                  <th style={thStyle}>Season</th>
                  <th style={thStyle}>Goalkeepers</th>
                  <th style={thStyle}>Benchmarkable</th>
                  <th style={thStyle}>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.contexts.map((c) => (
                  <tr key={`${c.competitionId}-${c.seasonId}`}>
                    <td style={tdStyle}>{c.competitionName}</td>
                    <td style={tdStyle}>{c.seasonName}</td>
                    <td className="tabular" style={tdStyle}>
                      {c.totalGoalkeepers}
                    </td>
                    <td className="tabular" style={tdStyle}>
                      {c.benchmarkableGoalkeepers}
                    </td>
                    <td style={{ ...tdStyle, color: STATUS_COLOR[c.status], fontWeight: 700 }}>
                      {STATUS_LABEL[c.status]}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
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
