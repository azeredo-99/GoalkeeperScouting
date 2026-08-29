import type { CSSProperties, ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { discoverPlayers, getCompetitions, getScoutingProfiles, getSeasons, searchPlayers } from "../api/client";
import type { NamedOption } from "../api/client";
import type { PerformanceRow, ScoutingProfile } from "../api/types";
import { PlayerResultCard } from "../components/PlayerResultCard";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { groupByPlayer, type PlayerEntity } from "../lib/players";
import { useCustomProfiles } from "../lib/customScoutingProfiles";
import { useNavigate, useSearchParams } from "react-router-dom";

type Mode = "search" | "discover";

type SortKey =
  | "minutes"
  | "marketValue"
  | "age"
  | "savePct"
  | "sweeperActionsP90"
  | "passSuccessPct"
  | "scoutingMatch";

const SORT_OPTIONS: { key: SortKey; label: string; get: (e: PlayerEntity) => number | null }[] = [
  { key: "minutes", label: "Minutes", get: (e) => e.primary.minutes },
  { key: "marketValue", label: "Market value", get: (e) => e.primary.marketValueEur },
  { key: "age", label: "Age", get: (e) => e.primary.age },
  { key: "savePct", label: "Save %", get: (e) => e.primary.metrics.shotStopping.savePct },
  { key: "sweeperActionsP90", label: "Sweeper actions /90", get: (e) => e.primary.metrics.sweeping.sweeperActionsP90 },
  { key: "passSuccessPct", label: "Pass success %", get: (e) => e.primary.metrics.distribution.passSuccessPct },
];

const SCOUTING_MATCH_SORT_OPTION: { key: SortKey; label: string; get: (e: PlayerEntity) => number | null } = {
  key: "scoutingMatch",
  label: "Scouting Match",
  get: (e) => e.primary.scoutingMatch?.matchScore ?? null,
};

const EMPTY_FILTERS = {
  minMinutes: "" as number | "",
  maxAge: "" as number | "",
  maxValue: "" as number | "",
  competitionId: "" as number | "",
  seasonId: "" as number | "",
  minSavePct: "" as number | "",
  minSweeperP90: "" as number | "",
  minPassPct: "" as number | "",
  minLongBallPct: "" as number | "",
};

export function Discover() {
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<Mode>("search");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PerformanceRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [compareSelection, setCompareSelection] = useState<PlayerEntity[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>("minutes");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [showPerformanceFilters, setShowPerformanceFilters] = useState(false);
  const navigate = useNavigate();

  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const setFilter = <K extends keyof typeof EMPTY_FILTERS>(key: K, value: (typeof EMPTY_FILTERS)[K]) =>
    setFilters((prev) => ({ ...prev, [key]: value }));

  const [competitions, setCompetitions] = useState<NamedOption[]>([]);
  const [seasons, setSeasons] = useState<NamedOption[]>([]);

  // "Scouting profile" -- opt-in, "None" por omissão. Só afeta o modo
  // "Discover by profile": quando ativo, cada resultado ganha
  // `scoutingMatch` (calculado no backend, ver discover_players) e o
  // sort "Scouting Match" fica disponível. Pode chegar pré-selecionado
  // vindo de /scouting-profiles ("Use profile") -- tanto para um
  // predefinido como para um perfil custom do scout (localStorage).
  const [scoutingProfiles, setScoutingProfiles] = useState<ScoutingProfile[]>([]);
  const [scoutingProfileId, setScoutingProfileId] = useState<string>(searchParams.get("scouting_profile") ?? "");
  const customProfiles = useCustomProfiles();

  // `scoutingProfileId` identifica UM perfil entre duas listas de
  // proveniência diferente (predefinidos do backend vs. custom do
  // scout, ambos guardados por id). Resolvido aqui, uma vez, para que
  // runDiscover nunca tenha de adivinhar de onde veio o id -- e para
  // que um id que já não existe em lado nenhum (ex.: perfil custom
  // apagado entretanto) seja detetável em vez de silenciosamente
  // enviado como "sem perfil".
  const selectedBuiltInProfile = useMemo(
    () => scoutingProfiles.find((p) => p.id === scoutingProfileId) ?? null,
    [scoutingProfiles, scoutingProfileId]
  );
  const selectedCustomProfile = useMemo(
    () => customProfiles.find((p) => p.id === scoutingProfileId) ?? null,
    [customProfiles, scoutingProfileId]
  );

  useEffect(() => {
    getCompetitions()
      .then((res) => setCompetitions(res.competitions))
      .catch(() => setCompetitions([]));
    getScoutingProfiles()
      .then((res) => setScoutingProfiles(res.profiles))
      .catch(() => setScoutingProfiles([]));
  }, []);

  useEffect(() => {
    if (scoutingProfileId) {
      setMode("discover");
    }
  }, [scoutingProfileId]);

  useEffect(() => {
    getSeasons(filters.competitionId === "" ? undefined : filters.competitionId)
      .then((res) => setSeasons(res.seasons))
      .catch(() => setSeasons([]));
  }, [filters.competitionId]);

  const entities = useMemo(() => (results ? groupByPlayer(results) : null), [results]);

  const sortOptions = useMemo(
    () => (scoutingProfileId ? [...SORT_OPTIONS, SCOUTING_MATCH_SORT_OPTION] : SORT_OPTIONS),
    [scoutingProfileId]
  );

  const sortedEntities = useMemo(() => {
    if (!entities) return entities;
    const spec = sortOptions.find((s) => s.key === sortKey) ?? sortOptions[0];
    const dir = sortDir === "asc" ? 1 : -1;
    return [...entities].sort((a, b) => {
      const av = spec.get(a);
      const bv = spec.get(b);
      if (av == null && bv == null) return 0;
      if (av == null) return 1; // missing values always sort last, regardless of direction
      if (bv == null) return -1;
      return (av - bv) * dir;
    });
  }, [entities, sortOptions, sortKey, sortDir]);

  // Guarda contra race conditions: se o utilizador escrever depressa,
  // várias pesquisas ficam pendentes ao mesmo tempo. Só o resultado da
  // ÚLTIMA pesquisa disparada pode atualizar o ecrã -- uma resposta
  // antiga a chegar depois de uma mais recente é descartada.
  const searchSeq = useRef(0);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  async function executeSearch(q: string) {
    const seq = ++searchSeq.current;

    if (!q.trim()) {
      setResults(null);
      setError(null);
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

  function onQueryChange(q: string) {
    setQuery(q);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => executeSearch(q), 250);
  }

  async function runDiscover() {
    setLoading(true);
    setError(null);
    try {
      if (scoutingProfileId && !selectedBuiltInProfile && !selectedCustomProfile) {
        throw new Error("The selected scouting profile is no longer available. Pick another one.");
      }
      const { results } = await discoverPlayers({
        competitionId: filters.competitionId === "" ? undefined : filters.competitionId,
        seasonId: filters.seasonId === "" ? undefined : filters.seasonId,
        minMinutes: filters.minMinutes === "" ? undefined : filters.minMinutes,
        maxAge: filters.maxAge === "" ? undefined : filters.maxAge,
        maxMarketValueEur: filters.maxValue === "" ? undefined : filters.maxValue * 1_000_000,
        minSavePct: filters.minSavePct === "" ? undefined : filters.minSavePct,
        minSweeperActionsP90: filters.minSweeperP90 === "" ? undefined : filters.minSweeperP90,
        minPassSuccessPct: filters.minPassPct === "" ? undefined : filters.minPassPct,
        minLongBallPct: filters.minLongBallPct === "" ? undefined : filters.minLongBallPct,
        scoutingProfileId: selectedBuiltInProfile ? scoutingProfileId : undefined,
        customProfile: selectedCustomProfile ?? undefined,
      });
      setResults(results);
      if (scoutingProfileId) setSortKey("scoutingMatch");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function clearFilters() {
    setFilters(EMPTY_FILTERS);
  }

  function rowMatches(a: PlayerEntity, b: PlayerEntity) {
    return a.playerName === b.playerName;
  }

  function toggleCompare(entity: PlayerEntity) {
    setCompareSelection((prev) => {
      const exists = prev.some((p) => rowMatches(p, entity));
      if (exists) return prev.filter((p) => !rowMatches(p, entity));
      if (prev.length >= 4) return prev;
      return [...prev, entity];
    });
  }

  function goToCompare() {
    const q = compareSelection
      .map((e) => `${e.playerName}:${e.primary.competitionId}:${e.primary.seasonId}`)
      .join(",");
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
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search goalkeeper…"
          style={inputStyle}
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <FilterGroup title="Player">
            <Field label="Max age">
              <input
                type="number"
                value={filters.maxAge}
                onChange={(e) => setFilter("maxAge", e.target.value === "" ? "" : Number(e.target.value))}
                style={smallInput}
              />
            </Field>
            <Field label="Max market value (€M)">
              <input
                type="number"
                value={filters.maxValue}
                onChange={(e) => setFilter("maxValue", e.target.value === "" ? "" : Number(e.target.value))}
                style={smallInput}
              />
            </Field>
          </FilterGroup>

          <FilterGroup title="Context">
            <Field label="Competition">
              <select
                value={filters.competitionId}
                onChange={(e) => {
                  const value = e.target.value === "" ? "" : Number(e.target.value);
                  setFilters((prev) => ({ ...prev, competitionId: value, seasonId: "" }));
                }}
                style={selectStyle}
              >
                <option value="">Any</option>
                {competitions.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Season">
              <select
                value={filters.seasonId}
                onChange={(e) => setFilter("seasonId", e.target.value === "" ? "" : Number(e.target.value))}
                style={selectStyle}
              >
                <option value="">Any</option>
                {seasons.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Min minutes">
              <input
                type="number"
                value={filters.minMinutes}
                onChange={(e) => setFilter("minMinutes", e.target.value === "" ? "" : Number(e.target.value))}
                style={smallInput}
              />
            </Field>
          </FilterGroup>

          <FilterGroup title="Scouting profile (optional)">
            <Field label="Match against">
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
                {customProfiles.length > 0 && (
                  <optgroup label="Custom">
                    {customProfiles.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </Field>
            {scoutingProfileId && (
              <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", maxWidth: 360 }}>
                Each result shows a Scouting Match against this profile — not a rating. Missing data is shown as
                insufficient, never as a poor match.
              </div>
            )}
          </FilterGroup>

          <div>
            <button onClick={() => setShowPerformanceFilters((v) => !v)} style={disclosureBtn}>
              {showPerformanceFilters ? "− Performance filters" : "+ Performance filters"}
            </button>
            {showPerformanceFilters && (
              <div style={{ marginTop: "var(--space-3)" }}>
                <FilterGroup title="Performance" muted>
                  <Field label="Min save %">
                    <input
                      type="number"
                      value={filters.minSavePct}
                      onChange={(e) => setFilter("minSavePct", e.target.value === "" ? "" : Number(e.target.value))}
                      style={smallInput}
                    />
                  </Field>
                  <Field label="Min sweeper actions /90">
                    <input
                      type="number"
                      step="0.1"
                      value={filters.minSweeperP90}
                      onChange={(e) => setFilter("minSweeperP90", e.target.value === "" ? "" : Number(e.target.value))}
                      style={smallInput}
                    />
                  </Field>
                  <Field label="Min pass success %">
                    <input
                      type="number"
                      value={filters.minPassPct}
                      onChange={(e) => setFilter("minPassPct", e.target.value === "" ? "" : Number(e.target.value))}
                      style={smallInput}
                    />
                  </Field>
                  <Field label="Min long ball %">
                    <input
                      type="number"
                      value={filters.minLongBallPct}
                      onChange={(e) =>
                        setFilter("minLongBallPct", e.target.value === "" ? "" : Number(e.target.value))
                      }
                      style={smallInput}
                    />
                  </Field>
                </FilterGroup>
              </div>
            )}
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={clearFilters} style={secondaryBtn}>
              Clear filters
            </button>
            <button onClick={runDiscover} style={runBtn}>
              Find goalkeepers
            </button>
          </div>
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

      {!loading && !error && sortedEntities && sortedEntities.length > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginTop: "var(--space-5)",
            fontSize: 12,
            color: "var(--color-text-secondary)",
          }}
        >
          <span>Sort by</span>
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
            style={{ ...selectStyle, width: "auto" }}
          >
            {sortOptions.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
          <button onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))} style={secondaryBtn}>
            {sortDir === "asc" ? "Ascending" : "Descending"}
          </button>
        </div>
      )}

      <div style={{ marginTop: "var(--space-3)", display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
        {loading && <LoadingState />}
        {error && (
          <ErrorState message={error} onRetry={mode === "search" ? () => executeSearch(query) : runDiscover} />
        )}
        {!loading && !error && sortedEntities && sortedEntities.length === 0 && (
          <EmptyState message="No goalkeepers matched. Adjust filters and try again." />
        )}
        {!loading &&
          !error &&
          sortedEntities?.map((entity) => (
            <PlayerResultCard
              key={entity.playerName}
              entity={entity}
              onToggleCompare={toggleCompare}
              selectedForCompare={compareSelection.some((p) => rowMatches(p, entity))}
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

function FilterGroup({ title, children, muted }: { title: string; children: ReactNode; muted?: boolean }) {
  return (
    <div
      className="card"
      style={{
        padding: "var(--space-4)",
        background: muted ? "var(--color-surface)" : undefined,
      }}
    >
      <div className="label" style={{ marginBottom: "var(--space-3)" }}>
        {title}
      </div>
      <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", alignItems: "flex-end" }}>
        {children}
      </div>
    </div>
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
  width: 130,
};

const selectStyle: CSSProperties = {
  padding: "8px 10px",
  fontSize: 13,
  fontWeight: 600,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
  width: 180,
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

const secondaryBtn: CSSProperties = {
  padding: "10px 16px",
  fontSize: 13,
  fontWeight: 600,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "transparent",
  color: "var(--color-text-secondary)",
  cursor: "pointer",
};

const disclosureBtn: CSSProperties = {
  padding: "6px 0",
  fontSize: 12,
  fontWeight: 600,
  border: "none",
  background: "transparent",
  color: "var(--color-text-tertiary)",
  cursor: "pointer",
};
