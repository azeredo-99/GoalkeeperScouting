import type { ReactNode } from "react";

export function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div
      style={{
        background: "var(--color-surface-raised)",
        border: "1px solid var(--color-border-soft)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-3) var(--space-4)",
      }}
    >
      <div className="label">{label}</div>
      <div
        className="tabular"
        style={{ fontSize: 20, fontWeight: 700, marginTop: 4, color: "var(--color-text)" }}
      >
        {value}
      </div>
      {hint && (
        <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 2 }}>
          {hint}
        </div>
      )}
    </div>
  );
}

export function MetricGroup({
  title,
  note,
  children,
}: {
  title: string;
  note?: string;
  children: ReactNode;
}) {
  return (
    <section style={{ marginBottom: "var(--space-6)" }}>
      <div className="section-title">{title}</div>
      {note && (
        <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginBottom: "var(--space-3)" }}>
          {note}
        </div>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "var(--space-3)",
        }}
      >
        {children}
      </div>
    </section>
  );
}
