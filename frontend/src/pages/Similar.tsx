import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getSimilarity } from "../api/client";
import type { SimilarityResponse } from "../api/types";
import { ContextBadge } from "../components/ContextBadge";
import { BackLink } from "../components/BackLink";
import { DimensionInline, DimensionSnapshot } from "../components/DimensionSnapshot";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { formatClub, formatMarketValue } from "../lib/format";

const NO_COMPARABLES_MESSAGE = "No suitable comparable goalkeepers found for this reference context.";

export function Similar() {
  const { player } = useParams<{ player: string }>();
  const navigate = useNavigate();
  const [weights, setWeights] = useState({ shotStopping: 30, distribution: 35, proactivity: 35 });
  const [data, setData] = useState<SimilarityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const total = weights.shotStopping + weights.distribution + weights.proactivity;

  function load() {
    if (!player) return;
    setLoading(true);
    setError(null);
    getSimilarity(player, weights)
      .then(setData)
      // A página de Similarity só falha por falta de comparáveis (jogador
      // sem minutos suficientes, sem métricas, etc.) -- nunca mostramos o
      // texto bruto do backend aqui (pode incluir mensagens internas em
      // português vindas de similarity_engine).
      .catch(() => setError(NO_COMPARABLES_MESSAGE))
      .finally(() => setLoading(false));
  }

  useEffect(load, [player]);

  if (loading && !data) return <LoadingState label="Loading similarity…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  return (
    <div>
      <BackLink label="Back to profile" to={`/player/${encodeURIComponent(data.target.playerName)}`} />
      <div className="label" style={{ marginBottom: 4 }}>
        Similar to
      </div>
      <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 8px" }}>{data.target.playerName}</h1>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-4)" }}>
        <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>{formatClub(data.target.club)}</span>
        <ContextBadge
          competitionName={data.target.competitionName}
          seasonName={data.target.seasonName}
          minutes={data.target.minutes}
        />
      </div>

      <div className="card" style={{ marginBottom: "var(--space-6)" }}>
        <div className="section-title">Reference profile</div>
        <DimensionSnapshot metrics={data.target.metrics} />
      </div>

      <div className="card" style={{ marginBottom: "var(--space-6)" }}>
        <div className="section-title">Similarity weights</div>
        <div style={{ display: "flex", gap: "var(--space-5)", flexWrap: "wrap" }}>
          <WeightSlider
            label="Shot Stopping"
            value={weights.shotStopping}
            onChange={(v) => setWeights((w) => ({ ...w, shotStopping: v }))}
          />
          <WeightSlider
            label="Distribution"
            value={weights.distribution}
            onChange={(v) => setWeights((w) => ({ ...w, distribution: v }))}
          />
          <WeightSlider
            label="Proactivity"
            value={weights.proactivity}
            onChange={(v) => setWeights((w) => ({ ...w, proactivity: v }))}
          />
        </div>
        <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 10 }}>
          Effective weight: Shot Stopping {((weights.shotStopping / total) * 100 || 0).toFixed(0)}% · Distribution{" "}
          {((weights.distribution / total) * 100 || 0).toFixed(0)}% · Proactivity{" "}
          {((weights.proactivity / total) * 100 || 0).toFixed(0)}%
        </div>
        <button
          onClick={load}
          disabled={total <= 0}
          style={{
            marginTop: "var(--space-4)",
            padding: "9px 16px",
            fontSize: 12,
            fontWeight: 700,
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--color-accent)",
            background: "var(--color-accent)",
            color: "#04150e",
            cursor: total <= 0 ? "not-allowed" : "pointer",
            opacity: total <= 0 ? 0.5 : 1,
          }}
        >
          Recalculate
        </button>
      </div>

      <div className="section-title">Results</div>
      {data.results.length === 0 ? (
        <EmptyState message="No suitable comparable goalkeepers found." />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          {data.results.map((r) => (
            <div key={`${r.playerName}-${r.competitionId}-${r.seasonId}`} className="card" style={{ padding: "var(--space-4)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-4)", flexWrap: "wrap" }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
                    <span style={{ fontWeight: 700, fontSize: 15 }}>
                      {r.rank}. {r.playerName}
                    </span>
                    <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>{formatClub(r.club)}</span>
                  </div>
                  <div style={{ marginTop: 6, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <ContextBadge competitionName={r.competitionName} seasonName={r.seasonName} minutes={r.minutes} />
                    <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{formatMarketValue(r.marketValueEur)}</span>
                  </div>
                  <div style={{ marginTop: "var(--space-3)" }}>
                    <DimensionInline metrics={r.metrics} />
                  </div>
                  <div className="label" style={{ marginTop: "var(--space-3)", marginBottom: 4 }}>
                    Why similar?
                  </div>
                  <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: 0, maxWidth: 560 }}>
                    {r.explanation}
                  </p>
                </div>
                <div style={{ textAlign: "right", flexShrink: 0 }}>
                  <div className="label">Similarity</div>
                  <div className="tabular" style={{ fontSize: 20, fontWeight: 800, color: "var(--color-accent-text)" }}>
                    {r.similarityPct.toFixed(1)}%
                  </div>
                  <button
                    onClick={() => navigate(`/player/${encodeURIComponent(r.playerName)}`)}
                    style={{
                      marginTop: 8,
                      padding: "6px 12px",
                      fontSize: 12,
                      fontWeight: 600,
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--color-border)",
                      background: "transparent",
                      color: "var(--color-text-secondary)",
                      cursor: "pointer",
                    }}
                  >
                    View profile
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function WeightSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>
        {label}
      </div>
      <input
        type="range"
        min={0}
        max={100}
        step={5}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ accentColor: "#22936b", width: 160 }}
      />
      <div className="tabular" style={{ fontSize: 12, fontWeight: 700 }}>
        {value}
      </div>
    </div>
  );
}
