export function ContextBadge({
  competitionName,
  seasonName,
  minutes,
}: {
  competitionName: string;
  seasonName: string;
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
      <span>{competitionName}</span>
      <span style={{ color: "var(--color-text-tertiary)" }}>·</span>
      <span>{seasonName}</span>
      {minutes != null && (
        <>
          <span style={{ color: "var(--color-text-tertiary)" }}>·</span>
          <span className="tabular">{minutes.toFixed(0)} min</span>
        </>
      )}
    </div>
  );
}

// Discreto de propósito -- a fonte é uma nota de proveniência, não uma
// segunda hierarquia visual. Só aparece para FBref (StatsBomb continua
// a ser o caso base, sem badge, ver PlayerProfile.tsx/ScoutingReport.tsx).
export function SourceBadge() {
  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        color: "var(--color-text-tertiary)",
        border: "1px solid var(--color-border-soft)",
        borderRadius: 4,
        padding: "2px 6px",
      }}
      title="This performance sample comes from FBref's aggregated season statistics, not StatsBomb event data — see Data Coverage for details."
    >
      Source: FBref
    </span>
  );
}

export type SampleSize = "unknown" | "large" | "medium" | "small";

export function sampleSize(minutes: number | null): SampleSize {
  return minutes == null ? "unknown" : minutes >= 900 ? "large" : minutes >= 450 ? "medium" : "small";
}

export function sampleSizeLabel(minutes: number | null): string {
  const size = sampleSize(minutes);
  return size === "large" ? "Strong sample" : size === "medium" ? "Moderate sample" : "Limited sample";
}

export function SampleIndicator({ minutes }: { minutes: number | null }) {
  const size = sampleSize(minutes);
  const color =
    size === "large"
      ? "var(--color-accent-text)"
      : size === "medium"
        ? "var(--color-text-secondary)"
        : "var(--color-warning)";
  return (
    <span style={{ fontSize: 11, fontWeight: 600, color }}>
      {sampleSizeLabel(minutes)} {minutes != null ? `(${minutes.toFixed(0)} min)` : ""}
    </span>
  );
}
