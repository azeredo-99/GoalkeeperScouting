export function ContextBadge({
  competitionId,
  seasonId,
  minutes,
}: {
  competitionId: number;
  seasonId: number;
  minutes?: number | null;
}) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: 12,
        fontWeight: 600,
        color: "var(--color-text-secondary)",
        background: "var(--color-surface-raised)",
        border: "1px solid var(--color-border-soft)",
        borderRadius: 999,
        padding: "4px 10px",
      }}
    >
      <span>Competition #{competitionId}</span>
      <span style={{ color: "var(--color-text-tertiary)" }}>·</span>
      <span>Season #{seasonId}</span>
      {minutes != null && (
        <>
          <span style={{ color: "var(--color-text-tertiary)" }}>·</span>
          <span className="tabular">{minutes.toFixed(0)} min</span>
        </>
      )}
    </div>
  );
}

export function SampleIndicator({ minutes }: { minutes: number | null }) {
  const size = minutes == null ? "unknown" : minutes >= 900 ? "large" : minutes >= 450 ? "medium" : "small";
  const color =
    size === "large"
      ? "var(--color-accent-text)"
      : size === "medium"
        ? "var(--color-text-secondary)"
        : "var(--color-danger)";
  const label =
    size === "large" ? "Robust sample" : size === "medium" ? "Moderate sample" : "Small sample";
  return (
    <span style={{ fontSize: 11, fontWeight: 600, color }}>
      {label} {minutes != null ? `(${minutes.toFixed(0)} min)` : ""}
    </span>
  );
}
