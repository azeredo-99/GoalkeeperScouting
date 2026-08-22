import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getPlayerProfile, getScoutingProfiles } from "../api/client";
import type { PlayerProfileResponse, ScoutingProfile } from "../api/types";
import { ShortlistItem } from "../components/ShortlistItem";
import { ErrorState, LoadingState } from "../components/States";
import type { PlayerEntity } from "../lib/players";
import { STATUS_LABELS, removeFromShortlist, useShortlist, type ShortlistEntry } from "../lib/shortlist";

type SortKey = "recent" | "name" | "marketValue" | "minutes" | "priority";

const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: "recent", label: "Recently added" },
  { key: "name", label: "Name" },
  { key: "marketValue", label: "Market value" },
  { key: "minutes", label: "Minutes" },
  { key: "priority", label: "Priority" },
];

const PRIORITY_RANK = { priority: 2, high: 1, normal: 0 } as const;

export function Shortlist() {
  const navigate = useNavigate();
  const entries = useShortlist();
  const [profiles, setProfiles] = useState<Record<string, PlayerProfileResponse>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("recent");

  // Contexto de sessão, NUNCA guardado no jogador ou no entry do
  // shortlist -- é só "que perfil estou a usar para olhar para esta
  // lista agora". Perde-se ao recarregar de propósito: reforça que
  // scouting match é sempre PLAYER × PROFILE × CONTEXT, nunca uma nota
  // permanente presa ao jogador.
  const [scoutingProfiles, setScoutingProfiles] = useState<ScoutingProfile[]>([]);
  const [scoutingProfileId, setScoutingProfileId] = useState("");

  useEffect(() => {
    getScoutingProfiles()
      .then((res) => setScoutingProfiles(res.profiles))
      .catch(() => setScoutingProfiles([]));
  }, []);

  // Só pede os perfis que ainda não temos em cache -- adicionar/remover
  // outro jogador nesta lista nunca refaz o pedido dos que já foram
  // carregados. Um pedido por jogador (não por métrica, não por
  // contexto): o shortlist é normalmente pequeno, e isto evita
  // benchmarking N+1 por já não pedir nada além do perfil base.
  const namesKey = entries.map((e) => e.playerName).sort().join("|");

  useEffect(() => {
    const missing = entries.filter((e) => !(e.playerName in profiles));
    if (missing.length === 0) return;
    setLoading(true);
    setError(null);
    Promise.allSettled(
      missing.map((e) => getPlayerProfile(e.playerName).then((profile) => [e.playerName, profile] as const))
    )
      .then((results) => {
        setProfiles((prev) => {
          const next = { ...prev };
          for (const result of results) {
            if (result.status === "fulfilled") {
              const [name, profile] = result.value;
              next[name] = profile;
            }
          }
          return next;
        });
        if (results.some((r) => r.status === "rejected")) {
          setError("Some shortlisted goalkeepers could not be loaded.");
        }
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namesKey]);

  function entityFor(entry: ShortlistEntry): PlayerEntity | null {
    const profile = profiles[entry.playerName];
    if (!profile) return null;
    const contexts = profile.performances;
    const primary =
      contexts.find((c) => c.competitionId === entry.competitionId && c.seasonId === entry.seasonId) ?? contexts[0];
    if (!primary) return null;
    return { playerName: entry.playerName, primary, contexts };
  }

  const rows = useMemo(() => {
    const withEntities = entries
      .map((entry) => ({ entry, entity: entityFor(entry) }))
      .filter((r): r is { entry: ShortlistEntry; entity: PlayerEntity } => r.entity !== null);

    const filtered = query.trim()
      ? withEntities.filter((r) => r.entry.playerName.toLowerCase().includes(query.trim().toLowerCase()))
      : withEntities;

    const sorted = [...filtered].sort((a, b) => {
      switch (sortKey) {
        case "name":
          return a.entry.playerName.localeCompare(b.entry.playerName);
        case "marketValue":
          return (b.entity.primary.marketValueEur ?? -1) - (a.entity.primary.marketValueEur ?? -1);
        case "minutes":
          return (b.entity.primary.minutes ?? -1) - (a.entity.primary.minutes ?? -1);
        case "priority":
          return PRIORITY_RANK[b.entry.priority] - PRIORITY_RANK[a.entry.priority] || b.entry.createdAt - a.entry.createdAt;
        case "recent":
        default:
          return b.entry.createdAt - a.entry.createdAt;
      }
    });

    return sorted;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entries, profiles, query, sortKey]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const e of entries) counts[e.status] = (counts[e.status] ?? 0) + 1;
    return counts;
  }, [entries]);
  const priorityCount = entries.filter((e) => e.priority === "priority").length;

  return (
    <div>
      <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 4px" }}>Shortlist</h1>
      <p style={{ color: "var(--color-text-secondary)", margin: "0 0 var(--space-3)" }}>Your selected goalkeepers.</p>

      {entries.length > 0 && (
        <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", marginBottom: "var(--space-5)", fontSize: 12 }}>
          <span style={{ fontWeight: 700 }}>
            {entries.length} {entries.length === 1 ? "goalkeeper" : "goalkeepers"}
          </span>
          {priorityCount > 0 && (
            <span style={{ color: "var(--color-accent-text)" }}>{priorityCount} priority</span>
          )}
          {(Object.keys(STATUS_LABELS) as (keyof typeof STATUS_LABELS)[])
            .filter((s) => s !== "watch" && statusCounts[s] > 0)
            .map((s) => (
              <span key={s} style={{ color: "var(--color-text-secondary)" }}>
                {statusCounts[s]} {STATUS_LABELS[s]}
              </span>
            ))}
          {statusCounts.watch > 0 && (
            <span style={{ color: "var(--color-text-tertiary)" }}>{statusCounts.watch} Watch</span>
          )}
        </div>
      )}

      {entries.length === 0 && (
        <div className="card" style={{ padding: "var(--space-6)", textAlign: "center" }}>
          <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 6 }}>Your shortlist is empty.</div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: "var(--space-4)" }}>
            Save goalkeepers from Discover or Player Profile to build your scouting list.
          </div>
          <button onClick={() => navigate("/discover")} style={ctaBtn}>
            Discover goalkeepers
          </button>
        </div>
      )}

      {entries.length > 0 && (
        <>
          <div
            className="card"
            style={{
              padding: "var(--space-3) var(--space-4)",
              marginBottom: "var(--space-4)",
              display: "flex",
              gap: "var(--space-4)",
              flexWrap: "wrap",
              alignItems: "center",
            }}
          >
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search shortlist…"
              style={searchStyle}
            />
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--color-text-secondary)" }}>
              <span>Sort by</span>
              <select value={sortKey} onChange={(e) => setSortKey(e.target.value as SortKey)} style={selectStyle}>
                {SORT_OPTIONS.map((o) => (
                  <option key={o.key} value={o.key}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--color-text-secondary)" }}>
              <span>Scouting profile</span>
              <select
                value={scoutingProfileId}
                onChange={(e) => setScoutingProfileId(e.target.value)}
                style={selectStyle}
              >
                <option value="">None</option>
                {scoutingProfiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {scoutingProfileId && (
            <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: -8, marginBottom: "var(--space-4)" }}>
              Viewing this list against a scouting profile — a per-session lens, not a saved player rating. Each
              goalkeeper is matched against this profile in their own performance context.
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {error && <ErrorState message={error} />}
            {rows.map(({ entry, entity }) => (
              <ShortlistItem
                key={entry.playerName}
                entry={entry}
                entity={entity}
                onRemove={() => removeFromShortlist(entry.playerName)}
                scoutingProfileId={scoutingProfileId || undefined}
              />
            ))}
            {loading && <LoadingState label="Loading shortlist…" />}
            {!loading && rows.length === 0 && entries.length > 0 && (
              <div style={{ fontSize: 13, color: "var(--color-text-tertiary)", padding: "var(--space-4)" }}>
                No shortlisted goalkeepers match "{query}".
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

const ctaBtn: CSSProperties = {
  padding: "10px 18px",
  fontSize: 13,
  fontWeight: 700,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-accent)",
  background: "var(--color-accent)",
  color: "#04150e",
  cursor: "pointer",
};

const searchStyle: CSSProperties = {
  flex: "1 1 220px",
  padding: "9px 12px",
  fontSize: 13,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
};

const selectStyle: CSSProperties = {
  padding: "7px 8px",
  fontSize: 12,
  fontWeight: 600,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
};
