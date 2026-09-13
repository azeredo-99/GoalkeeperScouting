import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";
import { getDataCoverage } from "../api/client";
import type { CoverageStatus, DataCoverageResponse, DataSource } from "../api/types";
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

const SOURCE_LABEL: Record<DataSource, string> = {
  statsbomb: "StatsBomb",
  fbref: "FBref",
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

  // Totais por fonte, calculados aqui a partir dos contextos já
  // devolvidos -- nenhum número novo do backend, só uma soma do que já
  // está na resposta (cada contexto já tem `source`, ver data_coverage.py).
  const sourceTotals = useMemo(() => {
    if (!data) return null;
    const totals: Record<DataSource, number> = { statsbomb: 0, fbref: 0 };
    for (const c of data.contexts) totals[c.source] += c.totalGoalkeepers;
    return totals;
  }, [data]);

  return (
    <div>
      <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 4px" }}>Data Coverage</h1>
      <p style={{ color: "var(--color-text-secondary)", margin: "0 0 var(--space-6)" }}>
        Internal view of what the system currently knows, per competition/season. Not a performance judgement.
      </p>

      {loading && <LoadingState label="Loading coverage…" />}
      {error && <ErrorState message={error} onRetry={load} />}

      {!loading && !error && data && sourceTotals && (
        <>
          <div style={{ display: "flex", gap: "var(--space-5)", marginBottom: "var(--space-4)" }}>
            <div>
              <div className="label">StatsBomb performances</div>
              <div className="tabular" style={{ fontSize: 20, fontWeight: 700 }}>
                {sourceTotals.statsbomb}
              </div>
            </div>
            <div>
              <div className="label">FBref performances</div>
              <div className="tabular" style={{ fontSize: 20, fontWeight: 700 }}>
                {sourceTotals.fbref}
              </div>
            </div>
          </div>

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
                  <th style={thStyle}>Source</th>
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
                    <td style={tdStyle}>{SOURCE_LABEL[c.source]}</td>
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

          <div
            className="card"
            style={{ marginTop: "var(--space-5)", fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.6 }}
          >
            <div className="section-title" style={{ marginBottom: "var(--space-2)" }}>
              About the two data sources
            </div>
            <p style={{ margin: "0 0 8px" }}>
              <strong>StatsBomb</strong> contexts are computed from raw match events. <strong>FBref</strong> contexts
              (the 2024/2025 seasons above) use FBref's own already-aggregated season statistics — Shot Stopping only;
              FBref's basic goalkeeping table does not include Sweeping or Distribution data, so those fields are left
              empty for FBref performances rather than shown as zero.
            </p>
            <p style={{ margin: "0 0 8px" }}>
              The two sources are never combined in the same benchmark or similarity comparison — each context
              belongs entirely to one source. But a metric with the same name isn't always the same definition:
              StatsBomb's <code>shots faced</code> counts every shot faced (on target or not); FBref's is{" "}
              <code>SoTA</code> (Shots on Target Against) only.
            </p>
            <p style={{ margin: 0 }}>
              Player identity is currently based on name matching, not a stable ID — the same goalkeeper can appear
              under a slightly different name spelling between sources (e.g. a full legal name in one, a shorter
              common name in the other) and won't automatically be linked as the same person.
            </p>
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
