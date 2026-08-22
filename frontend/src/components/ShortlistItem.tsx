import type { CSSProperties, ReactNode } from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { PlayerEntity } from "../lib/players";
import { getScoutingMatch } from "../api/client";
import type { ScoutingMatch } from "../api/types";
import { formatClub, formatMarketValue, formatPct, formatRateP90 } from "../lib/format";
import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  setNote,
  setPriority,
  setStatus,
  type Priority,
  type ScoutingStatus,
  type ShortlistEntry,
} from "../lib/shortlist";
import { ContextBadge } from "./ContextBadge";

// Cartão dedicado ao workspace da Shortlist -- inspirado no visual do
// PlayerResultCard (mesmo ContextBadge, mesmos botões, mesma tipografia
// tabular para números), mas reorganizado em linhas para caber
// prioridade/estado/nota sem sobrecarregar uma única linha flex.
export function ShortlistItem({
  entry,
  entity,
  onRemove,
  scoutingProfileId,
}: {
  entry: ShortlistEntry;
  entity: PlayerEntity;
  onRemove: () => void;
  scoutingProfileId?: string;
}) {
  const navigate = useNavigate();
  const { primary, contexts } = entity;
  const extraContexts = contexts.length - 1;
  const [note, setNoteLocal] = useState(entry.note);

  // Match calculado ao vivo para ESTE jogador + ESTE perfil + O
  // contexto de performance apresentado aqui -- nunca lido de um campo
  // gravado no jogador. Muda o perfil na página-mãe e este pedido
  // refaz-se sozinho.
  const [scoutingMatch, setScoutingMatch] = useState<ScoutingMatch | null>(null);
  useEffect(() => {
    if (!scoutingProfileId) {
      setScoutingMatch(null);
      return;
    }
    let cancelled = false;
    getScoutingMatch(entity.playerName, scoutingProfileId, primary.competitionId, primary.seasonId)
      .then((result) => {
        if (!cancelled) setScoutingMatch(result);
      })
      .catch(() => {
        if (!cancelled) setScoutingMatch(null);
      });
    return () => {
      cancelled = true;
    };
  }, [scoutingProfileId, entity.playerName, primary.competitionId, primary.seasonId]);

  function goToCompare() {
    const q = `${entity.playerName}:${primary.competitionId}:${primary.seasonId}`;
    navigate(`/compare?players=${encodeURIComponent(q)}`);
  }

  function commitNote() {
    if (note !== entry.note) setNote(entity.playerName, note);
  }

  return (
    <div className="card" style={{ padding: "var(--space-4)" }}>
      {/* ROW 1 -- identity + actions */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-4)", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ fontSize: 15, fontWeight: 700 }}>{entity.playerName}</span>
          <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>{formatClub(primary.club)}</span>
          {primary.age != null && (
            <span style={{ fontSize: 12, color: "var(--color-text-tertiary)" }}>{primary.age}y</span>
          )}
          {entry.priority !== "normal" && (
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: 999,
                color: entry.priority === "priority" ? "var(--color-accent-text)" : "var(--color-text-secondary)",
                background: entry.priority === "priority" ? "var(--color-accent-soft)" : "var(--color-surface-raised)",
                border: entry.priority === "priority" ? "1px solid var(--color-accent)" : "1px solid var(--color-border-soft)",
              }}
            >
              {PRIORITY_LABELS[entry.priority]}
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={() => navigate(`/player/${encodeURIComponent(entity.playerName)}`)} style={btnPrimary}>
            View profile
          </button>
          <button onClick={goToCompare} style={btnSecondary}>
            Compare
          </button>
          <button onClick={onRemove} style={btnSecondary}>
            Remove
          </button>
        </div>
      </div>

      {/* ROW 2 -- context + performance snapshot */}
      <div
        style={{
          marginTop: "var(--space-3)",
          display: "flex",
          alignItems: "center",
          gap: "var(--space-5)",
          flexWrap: "wrap",
          rowGap: "var(--space-2)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <ContextBadge competitionName={primary.competitionName} seasonName={primary.seasonName} minutes={primary.minutes} />
          {extraContexts > 0 && (
            <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>
              +{extraContexts} more performance {extraContexts === 1 ? "context" : "contexts"}
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: "var(--space-4)", marginLeft: "auto" }}>
          <Stat label="Market value" value={formatMarketValue(primary.marketValueEur)} />
          <Stat label="Save %" value={formatPct(primary.metrics.shotStopping.savePct)} />
          <Stat label="Sweeper /90" value={formatRateP90(primary.metrics.sweeping.sweeperActionsP90)} />
          <Stat label="Pass %" value={formatPct(primary.metrics.distribution.passSuccessPct)} />
        </div>
      </div>

      {scoutingProfileId && scoutingMatch && (
        <div style={{ marginTop: "var(--space-2)" }}>
          <ShortlistMatchBadge match={scoutingMatch} />
        </div>
      )}

      {/* ROW 3 -- scouting workflow: priority, status, note */}
      <div
        style={{
          marginTop: "var(--space-4)",
          paddingTop: "var(--space-3)",
          borderTop: "1px solid var(--color-border-soft)",
          display: "flex",
          gap: "var(--space-4)",
          alignItems: "flex-start",
          flexWrap: "wrap",
        }}
      >
        <Field label="Priority">
          <select
            value={entry.priority}
            onChange={(e) => setPriority(entity.playerName, e.target.value as Priority)}
            style={selectStyle}
          >
            {(Object.keys(PRIORITY_LABELS) as Priority[]).map((p) => (
              <option key={p} value={p}>
                {PRIORITY_LABELS[p]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Status">
          <select
            value={entry.status}
            onChange={(e) => setStatus(entity.playerName, e.target.value as ScoutingStatus)}
            style={selectStyle}
          >
            {(Object.keys(STATUS_LABELS) as ScoutingStatus[]).map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </Field>
        <div style={{ flex: "1 1 240px", minWidth: 200 }}>
          <div className="label" style={{ marginBottom: 4 }}>
            Note
          </div>
          <textarea
            value={note}
            onChange={(e) => setNoteLocal(e.target.value)}
            onBlur={commitNote}
            placeholder="Add scouting note…"
            rows={2}
            style={noteStyle}
          />
        </div>
      </div>
    </div>
  );
}

function ShortlistMatchBadge({ match }: { match: ScoutingMatch }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, flexWrap: "wrap" }}>
      <span style={{ color: "var(--color-text-tertiary)", fontWeight: 600 }}>
        Scouting Match ({match.profileName}):
      </span>
      <span style={{ color: "var(--color-accent-text)", fontWeight: 700 }}>{match.matchedCount} matched</span>
      {match.unmetCount > 0 && (
        <span style={{ color: "var(--color-warning)", fontWeight: 700 }}>{match.unmetCount} unmet</span>
      )}
      {match.insufficientCount > 0 && (
        <span style={{ color: "var(--color-text-tertiary)", fontWeight: 700 }}>
          {match.insufficientCount} insufficient data
        </span>
      )}
      {match.matchScore != null && (
        <span className="tabular" style={{ color: "var(--color-text-secondary)" }}>
          ({match.matchScore.toFixed(0)}%)
        </span>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ textAlign: "right" }}>
      <div className="label">{label}</div>
      <div className="tabular" style={{ fontWeight: 700, fontSize: 13 }}>
        {value}
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

const selectStyle: CSSProperties = {
  padding: "6px 8px",
  fontSize: 12,
  fontWeight: 600,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
  width: 130,
};

const noteStyle: CSSProperties = {
  width: "100%",
  resize: "vertical",
  padding: "8px 10px",
  fontSize: 12,
  fontFamily: "inherit",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
};
