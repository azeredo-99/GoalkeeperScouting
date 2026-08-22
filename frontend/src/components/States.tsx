export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div style={{ padding: "var(--space-6)", color: "var(--color-text-tertiary)", fontSize: 13 }}>
      {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      style={{
        padding: "var(--space-4)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-danger)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "var(--space-4)",
        flexWrap: "wrap",
      }}
    >
      <span style={{ color: "var(--color-danger)", fontSize: 13 }}>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            fontSize: 12,
            fontWeight: 600,
            padding: "6px 12px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--color-danger)",
            background: "transparent",
            color: "var(--color-danger)",
            cursor: "pointer",
            flexShrink: 0,
          }}
        >
          Try again
        </button>
      )}
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
