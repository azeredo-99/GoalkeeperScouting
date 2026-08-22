import type { CSSProperties } from "react";
import { useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { searchPlayers } from "../api/client";
import type { PerformanceRow } from "../api/types";
import { groupByPlayer, pickPrimaryContext, type PlayerEntity } from "../lib/players";
import { RadarChart } from "../components/RadarChart";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import {
  NO_ACTIONS_LABEL,
  formatClub,
  formatCount,
  formatDistance,
  formatMarketValue,
  formatPct,
  formatRateP90,
} from "../lib/format";

const COLORS = ["#22936b", "#c98a3f", "#4f7cc9", "#a464c9"];
const MAX_PLAYERS = 4;

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

interface Slot {
  playerName: string;
  contexts: PerformanceRow[] | null; // null while loading
  contextIndex: number;
  error: string | null;
}

function initialSlotsFromParams(raw: string | null): { playerName: string; competitionId: number; seasonId: number }[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((chunk) => {
      const [playerName, competitionId, seasonId] = chunk.split(":");
      return { playerName, competitionId: Number(competitionId), seasonId: Number(seasonId) };
    })
    .filter((s) => s.playerName)
    .slice(0, MAX_PLAYERS);
}

export function Compare() {
  const [params] = useSearchParams();
  const initialRequests = useMemo(() => initialSlotsFromParams(params.get("players")), []);

  const [slots, setSlots] = useState<Slot[]>(
    initialRequests.map((r) => ({ playerName: r.playerName, contexts: null, contextIndex: 0, error: null }))
  );
  const [initializing, setInitializing] = useState(initialRequests.length > 0);

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<PlayerEntity[] | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const searchSeq = useRef(0);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const didInit = useRef(false);
  if (!didInit.current && initialRequests.length > 0) {
    didInit.current = true;
    Promise.all(
      initialRequests.map(async (r) => {
        try {
          const { results } = await searchPlayers(r.playerName);
          const contexts = results.filter((row) => row.playerName === r.playerName);
          if (contexts.length === 0) throw new Error("No performance data for this goalkeeper.");
          let idx = contexts.findIndex(
            (c) => c.competitionId === r.competitionId && c.seasonId === r.seasonId
          );
          if (idx < 0) idx = contexts.indexOf(pickPrimaryContext(contexts));
          return { playerName: r.playerName, contexts, contextIndex: idx, error: null } as Slot;
        } catch (e) {
          return { playerName: r.playerName, contexts: null, contextIndex: 0, error: (e as Error).message } as Slot;
        }
      })
    ).then((resolved) => {
      setSlots(resolved);
      setInitializing(false);
    });
  }

  async function runSearch(q: string) {
    const seq = ++searchSeq.current;
    if (!q.trim()) {
      setSearchResults(null);
      setSearchError(null);
      return;
    }
    setSearchLoading(true);
    setSearchError(null);
    try {
      const { results } = await searchPlayers(q);
      if (seq === searchSeq.current) setSearchResults(groupByPlayer(results));
    } catch (e) {
      if (seq === searchSeq.current) setSearchError((e as Error).message);
    } finally {
      if (seq === searchSeq.current) setSearchLoading(false);
    }
  }

  function onQueryChange(q: string) {
    setQuery(q);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => runSearch(q), 250);
  }

  function addPlayer(entity: PlayerEntity) {
    if (slots.length >= MAX_PLAYERS) return;
    if (slots.some((s) => s.playerName === entity.playerName)) return;
    const idx = entity.contexts.indexOf(entity.primary);
    setSlots((prev) => [
      ...prev,
      { playerName: entity.playerName, contexts: entity.contexts, contextIndex: idx, error: null },
    ]);
  }

  function removePlayer(playerName: string) {
    setSlots((prev) => prev.filter((s) => s.playerName !== playerName));
  }

  function changeContext(playerName: string, newIndex: number) {
    setSlots((prev) => prev.map((s) => (s.playerName === playerName ? { ...s, contextIndex: newIndex } : s)));
  }

  const readySlots = slots.filter((s) => s.contexts && s.contexts.length > 0);
  const activeRows = readySlots.map((s) => s.contexts![s.contextIndex]);

  const nameCounts = activeRows.reduce<Record<string, number>>((acc, p) => {
    acc[p.playerName] = (acc[p.playerName] ?? 0) + 1;
    return acc;
  }, {});
  const displayName = (p: PerformanceRow) =>
    nameCounts[p.playerName] > 1 ? `${p.playerName} (${p.competitionName} · ${p.seasonName})` : p.playerName;

  return (
    <div>
      <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 4px" }}>Compare Goalkeepers</h1>
      <p style={{ color: "var(--color-text-secondary)", margin: "0 0 var(--space-5)" }}>
        Select up to {MAX_PLAYERS} goalkeepers.
      </p>

      {slots.length < MAX_PLAYERS && (
        <div style={{ marginBottom: "var(--space-5)" }}>
          <input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Search goalkeeper…"
            style={inputStyle}
          />
          {searchLoading && <div style={{ marginTop: 8 }}><LoadingState /></div>}
          {searchError && (
            <div style={{ marginTop: 8 }}>
              <ErrorState message={searchError} onRetry={() => runSearch(query)} />
            </div>
          )}
          {!searchLoading && !searchError && searchResults && searchResults.length === 0 && (
            <div style={{ marginTop: 8 }}>
              <EmptyState message="No goalkeepers matched." />
            </div>
          )}
          {!searchLoading && !searchError && searchResults && searchResults.length > 0 && (
            <div
              className="card"
              style={{ marginTop: 8, padding: "var(--space-2)", display: "flex", flexDirection: "column", gap: 4 }}
            >
              {searchResults.map((entity) => {
                const already = slots.some((s) => s.playerName === entity.playerName);
                return (
                  <button
                    key={entity.playerName}
                    onClick={() => !already && addPlayer(entity)}
                    disabled={already}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "8px 10px",
                      borderRadius: "var(--radius-sm)",
                      border: "none",
                      background: "transparent",
                      color: already ? "var(--color-text-tertiary)" : "var(--color-text)",
                      fontSize: 13,
                      cursor: already ? "default" : "pointer",
                      textAlign: "left",
                    }}
                  >
                    <span>
                      <strong>{entity.playerName}</strong>{" "}
                      <span style={{ color: "var(--color-text-secondary)" }}>{formatClub(entity.primary.club)}</span>
                    </span>
                    <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>
                      {already ? "Added" : "Add"}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
      {slots.length >= MAX_PLAYERS && (
        <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginBottom: "var(--space-5)" }}>
          Maximum of {MAX_PLAYERS} goalkeepers reached. Remove one to add another.
        </div>
      )}

      {initializing && <LoadingState label="Loading comparison…" />}

      {!initializing && slots.length === 0 && (
        <EmptyState message="Search and add up to four goalkeepers to start a comparison." />
      )}

      {!initializing && slots.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(auto-fit, minmax(220px, 1fr))`,
            gap: "var(--space-4)",
            marginBottom: "var(--space-6)",
          }}
        >
          {slots.map((slot, i) => (
            <div key={slot.playerName} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ width: 8, height: 8, borderRadius: 4, background: COLORS[i], marginBottom: 8 }} />
                <button onClick={() => removePlayer(slot.playerName)} style={removeBtn} aria-label={`Remove ${slot.playerName}`}>
                  Remove
                </button>
              </div>
              <div style={{ fontWeight: 700, fontSize: 15 }}>{slot.playerName}</div>
              {slot.error && (
                <div style={{ fontSize: 12, color: "var(--color-danger)", marginTop: 8 }}>{slot.error}</div>
              )}
              {slot.contexts && (
                <>
                  <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 8 }}>
                    {formatClub(slot.contexts[slot.contextIndex].club)}
                  </div>
                  {slot.contexts.length > 1 ? (
                    <select
                      value={slot.contextIndex}
                      onChange={(e) => changeContext(slot.playerName, Number(e.target.value))}
                      style={selectStyle}
                    >
                      {slot.contexts.map((c, ci) => (
                        <option key={`${c.competitionId}-${c.seasonId}`} value={ci}>
                          {c.competitionName} — {c.seasonName}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <div style={{ fontSize: 13, fontWeight: 600 }}>
                      {slot.contexts[0].competitionName} — {slot.contexts[0].seasonName}
                    </div>
                  )}
                  <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 6 }} className="tabular">
                    {slot.contexts[slot.contextIndex].minutes != null
                      ? `${slot.contexts[slot.contextIndex].minutes!.toFixed(0)} minutes`
                      : "Minutes unavailable"}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {!initializing && slots.length === 1 && (
        <EmptyState message="Add another goalkeeper to compare." />
      )}

      {!initializing && activeRows.length >= 2 && (
        <>
          <div style={{ marginBottom: "var(--space-6)" }}>
            <div className="section-title">Performance radar</div>
            <RadarChart
              labels={RADAR_LABELS}
              series={activeRows.map((p, i) => ({ name: displayName(p), color: COLORS[i], values: radarValues(p) }))}
              emptyMessage="Not enough recorded metrics for a radar in this comparison."
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
                      {activeRows.map((p) => (
                        <th key={`${p.playerName}-${p.competitionId}-${p.seasonId}`} style={thStyle}>
                          {displayName(p)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {group.metrics.map((metric) => (
                      <tr key={metric.label}>
                        <td style={tdLabelStyle}>{metric.label}</td>
                        {activeRows.map((p) => (
                          <td key={`${p.playerName}-${p.competitionId}-${p.seasonId}`} className="tabular" style={tdStyle}>
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
        </>
      )}
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

const selectStyle: CSSProperties = {
  padding: "6px 8px",
  fontSize: 12,
  fontWeight: 600,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
  width: "100%",
};

const removeBtn: CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  padding: "4px 8px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "transparent",
  color: "var(--color-text-secondary)",
  cursor: "pointer",
};

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
