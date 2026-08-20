import type { CSSProperties, ReactNode } from "react";
import { useRef, useState } from "react";
import { discoverPlayers, searchPlayers } from "../api/client";
import type { PerformanceRow } from "../api/types";
import { PlayerResultCard } from "../components/PlayerResultCard";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useNavigate } from "react-router-dom";

type Mode = "search" | "discover";

export function Discover() {
  const [mode, setMode] = useState<Mode>("search");
  const [query, setQuery] = useState("");
  const [minMinutes, setMinMinutes] = useState<number | "">("");
  const [maxAge, setMaxAge] = useState<number | "">("");
  const [maxValue, setMaxValue] = useState<number | "">("");
  const [results, setResults] = useState<PerformanceRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [compareSelection, setCompareSelection] = useState<PerformanceRow[]>([]);
  const navigate = useNavigate();

  // Guarda contra race conditions: se o utilizador escrever depressa,
  // várias pesquisas ficam pendentes ao mesmo tempo. Só o resultado da
  // ÚLTIMA pesquisa disparada pode atualizar o ecrã -- uma resposta
  // antiga a chegar depois de uma mais recente é descartada.
  const searchSeq = useRef(0);

  async function runSearch(q: string) {
    setQuery(q);
    const seq = ++searchSeq.current;

    if (!q.trim()) {
      setResults(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { results } = await searchPlayers(q);
      if (seq === searchSeq.current) setResults(results);
    } catch (e) {
      if (seq === searchSeq.current) setError((e as Error).message);
    } finally {
      if (seq === searchSeq.current) setLoading(false);
    }
  }

  async function runDiscover() {
    setLoading(true);
    setError(null);
    try {
      const { results } = await discoverPlayers({
        minMinutes: minMinutes === "" ? undefined : minMinutes,
        maxAge: maxAge === "" ? undefined : maxAge,
        maxMarketValueEur: maxValue === "" ? undefined : maxValue * 1_000_000,
      });
      setResults(results);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function toggleCompare(row: PerformanceRow) {
    setCompareSelection((prev) => {
      const exists = prev.some(
        (p) => p.playerName === row.playerName && p.competitionId === row.competitionId && p.seasonId === row.seasonId
      );
      if (exists) return prev.filter((p) => p !== row);
      if (prev.length >= 4) return prev;
      return [...prev, row];
    });
  }

  function goToCompare() {
    const q = compareSelection.map((r) => `${r.playerName}:${r.competitionId}:${r.seasonId}`).join(",");
    navigate(`/compare?players=${encodeURIComponent(q)}`);
  }

  return (
    <div>
      <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 4px" }}>Discover</h1>
      <p style={{ color: "var(--color-text-secondary)", margin: "0 0 var(--space-6)" }}>
        Find a specific goalkeeper, or discover candidates that fit a profile.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: "var(--space-5)" }}>
        <ModeButton
          active={mode === "search"}
          onClick={() => {
            setMode("search");
            setResults(null);
            setError(null);
          }}
          label="Search player"
        />
        <ModeButton
          active={mode === "discover"}
          onClick={() => {
            setMode("discover");
            setResults(null);
            setError(null);
          }}
          label="Discover by profile"
        />
      </div>

      {mode === "search" ? (
        <input
          value={query}
          onChange={(e) => runSearch(e.target.value)}
          placeholder="Search goalkeeper…"
          style={inputStyle}
        />
      ) : (
        <div className="card" style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", alignItems: "flex-end" }}>
          <Field label="Min minutes">
            <input
              type="number"
              value={minMinutes}
              onChange={(e) => setMinMinutes(e.target.value === "" ? "" : Number(e.target.value))}
              style={smallInput}
            />
          </Field>
          <Field label="Max age">
            <input
              type="number"
              value={maxAge}
              onChange={(e) => setMaxAge(e.target.value === "" ? "" : Number(e.target.value))}
              style={smallInput}
            />
          </Field>
          <Field label="Max value (€M)">
            <input
              type="number"
              value={maxValue}
              onChange={(e) => setMaxValue(e.target.value === "" ? "" : Number(e.target.value))}
              style={smallInput}
            />
          </Field>
          <button onClick={runDiscover} style={runBtn}>
            Find goalkeepers
          </button>
        </div>
      )}

      {compareSelection.length > 0 && (
        <div
          className="card"
          style={{ marginTop: "var(--space-4)", display: "flex", justifyContent: "space-between", alignItems: "center" }}
        >
          <span style={{ fontSize: 13 }}>
            {compareSelection.length}/4 selected: {compareSelection.map((p) => p.playerName).join(", ")}
          </span>
          <button disabled={compareSelection.length < 2} onClick={goToCompare} style={runBtn}>
            Compare selected
          </button>
        </div>
      )}

      <div style={{ marginTop: "var(--space-5)", display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
        {loading && <LoadingState />}
        {error && <ErrorState message={error} />}
        {!loading && results && results.length === 0 && <EmptyState message="No goalkeepers matched." />}
        {!loading &&
          results?.map((row) => (
            <PlayerResultCard
              key={`${row.playerName}-${row.competitionId}-${row.seasonId}`}
              row={row}
              onToggleCompare={toggleCompare}
              selectedForCompare={compareSelection.includes(row)}
            />
          ))}
      </div>
    </div>
  );
}

function ModeButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "10px 16px",
        borderRadius: "var(--radius-sm)",
        fontSize: 13,
        fontWeight: 700,
        cursor: "pointer",
        border: active ? "1px solid var(--color-accent)" : "1px solid var(--color-border)",
        background: active ? "var(--color-accent-soft)" : "transparent",
        color: active ? "var(--color-accent-text)" : "var(--color-text-secondary)",
      }}
    >
      {label}
    </button>
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

const inputStyle: CSSProperties = {
  width: "100%",
  padding: "14px 16px",
  fontSize: 15,
  borderRadius: "var(--radius-md)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface)",
  color: "var(--color-text)",
};

const smallInput: CSSProperties = {
  padding: "8px 10px",
  fontSize: 13,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
  width: 110,
};

const runBtn: CSSProperties = {
  padding: "10px 16px",
  fontSize: 13,
  fontWeight: 700,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-accent)",
  background: "var(--color-accent)",
  color: "#04150e",
  cursor: "pointer",
};
