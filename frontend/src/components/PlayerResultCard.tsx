import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import type { PlayerEntity } from "../lib/players";
import type { ScoutingMatch } from "../api/types";
import { formatClub, formatMarketValue, formatPct, formatRateP90 } from "../lib/format";
import { addToShortlist, removeFromShortlist, useIsShortlisted } from "../lib/shortlist";
import { ContextBadge } from "./ContextBadge";

// O Discovery mostra o guarda-redes como entidade única (ver
// lib/players.groupByPlayer) -- as estatísticas de topo vêm da amostra
// de mais minutos (`entity.primary`), e os restantes contextos ficam
// indicados discretamente em vez de duplicar o resultado.
export function PlayerResultCard({
  entity,
  onToggleCompare,
  selectedForCompare,
  onCompare,
  onRemove,
  showShortlistToggle = true,
  scoutingProfileId,
}: {
  entity: PlayerEntity;
  onToggleCompare?: (entity: PlayerEntity) => void;
  selectedForCompare?: boolean;
  onCompare?: (entity: PlayerEntity) => void;
  onRemove?: (entity: PlayerEntity) => void;
  showShortlistToggle?: boolean;
  // Perfil ativo em Discover (predefinido ou custom, é só o id em
  // qualquer dos casos) -- propagado para o Player Profile para que o
  // Scouting Report, mais à frente, o consiga mostrar. Sem isto, a
  // secção "Scouting Profile" do relatório nunca era alcançável a
  // partir da navegação normal.
  scoutingProfileId?: string;
}) {
  const navigate = useNavigate();
  const { primary, contexts } = entity;
  const extraContexts = contexts.length - 1;
  const shortlisted = useIsShortlisted(entity.playerName);

  function toggleShortlist() {
    if (shortlisted) {
      removeFromShortlist(entity.playerName);
    } else {
      addToShortlist(entity.playerName, primary.competitionId, primary.seasonId);
    }
  }

  return (
    <div
      className="card"
      style={{
        padding: "var(--space-4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "var(--space-4)",
        flexWrap: "wrap",
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ fontSize: 15, fontWeight: 700 }}>{entity.playerName}</span>
          <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>{formatClub(primary.club)}</span>
          {primary.age != null && (
            <span style={{ fontSize: 12, color: "var(--color-text-tertiary)" }}>{primary.age}y</span>
          )}
        </div>
        <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <ContextBadge
            competitionName={primary.competitionName}
            seasonName={primary.seasonName}
            minutes={primary.minutes}
          />
          {extraContexts > 0 && (
            <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>
              +{extraContexts} more performance {extraContexts === 1 ? "context" : "contexts"} available
            </span>
          )}
        </div>
        {primary.scoutingMatch && <ScoutingMatchBadge match={primary.scoutingMatch} />}
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-5)",
          flexWrap: "wrap",
          maxWidth: "100%",
          rowGap: "var(--space-3)",
        }}
      >
        <div style={{ textAlign: "right" }}>
          <div className="label">Market value</div>
          <div className="tabular" style={{ fontWeight: 700 }}>
            {formatMarketValue(primary.marketValueEur)}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="label">Save %</div>
          <div className="tabular" style={{ fontWeight: 700 }}>
            {formatPct(primary.metrics.shotStopping.savePct)}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="label">Sweeper /90</div>
          <div className="tabular" style={{ fontWeight: 700 }}>
            {formatRateP90(primary.metrics.sweeping.sweeperActionsP90)}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="label">Pass %</div>
          <div className="tabular" style={{ fontWeight: 700 }}>
            {formatPct(primary.metrics.distribution.passSuccessPct)}
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            onClick={() => {
              const q = scoutingProfileId ? `?scouting_profile=${encodeURIComponent(scoutingProfileId)}` : "";
              navigate(`/player/${encodeURIComponent(entity.playerName)}${q}`);
            }}
            style={btnPrimary}
          >
            View profile
          </button>
          {onToggleCompare && (
            <button
              onClick={() => onToggleCompare(entity)}
              style={selectedForCompare ? btnSecondaryActive : btnSecondary}
            >
              {selectedForCompare ? "Selected" : "Compare"}
            </button>
          )}
          {onCompare && (
            <button onClick={() => onCompare(entity)} style={btnSecondary}>
              Compare
            </button>
          )}
          {showShortlistToggle && (
            <button onClick={toggleShortlist} style={shortlisted ? btnSecondaryActive : btnSecondary}>
              {shortlisted ? "Added to shortlist" : "Add to shortlist"}
            </button>
          )}
          {onRemove && (
            <button onClick={() => onRemove(entity)} style={btnSecondary}>
              Remove
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Insígnia compacta do Scouting Match -- nunca uma "nota" do jogador.
// Mostra contagens (matched/unmet/insufficient) e, se houver
// preferências avaliáveis, uma percentagem secundária e explicável.
// Dados em falta aparecem sempre como "insufficient", nunca como mau
// resultado.
function ScoutingMatchBadge({ match }: { match: ScoutingMatch }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        marginTop: 6,
        fontSize: 11,
        flexWrap: "wrap",
      }}
    >
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
