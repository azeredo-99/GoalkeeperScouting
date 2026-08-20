export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div style={{ padding: "var(--space-6)", color: "var(--color-text-tertiary)", fontSize: 13 }}>
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div
      style={{
        padding: "var(--space-4)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-danger)",
        color: "var(--color-danger)",
        fontSize: 13,
      }}
    >
      {message}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div
      style={{
        padding: "var(--space-5)",
        borderRadius: "var(--radius-md)",
        border: "1px dashed var(--color-border)",
        color: "var(--color-text-tertiary)",
        fontSize: 13,
        textAlign: "center",
      }}
    >
      {message}
    </div>
  );
}
