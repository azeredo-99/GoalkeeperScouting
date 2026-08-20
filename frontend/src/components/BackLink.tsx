import { useNavigate } from "react-router-dom";

export function BackLink({ label = "Back", to }: { label?: string; to?: string }) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => (to ? navigate(to) : navigate(-1))}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        background: "none",
        border: "none",
        color: "var(--color-text-secondary)",
        fontSize: 13,
        fontWeight: 600,
        cursor: "pointer",
        padding: 0,
        marginBottom: "var(--space-4)",
      }}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {label}
    </button>
  );
}
