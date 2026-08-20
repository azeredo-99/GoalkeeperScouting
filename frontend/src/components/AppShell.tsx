import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/discover", label: "Discover" },
  { to: "/compare", label: "Compare" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 232,
          flexShrink: 0,
          borderRight: "1px solid var(--color-border)",
          padding: "var(--space-5) var(--space-4)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ marginBottom: "var(--space-7)" }}>
          <div style={{ fontSize: 15, fontWeight: 800, letterSpacing: "0.02em" }}>GOALKEEPER</div>
          <div
            style={{
              fontSize: 15,
              fontWeight: 800,
              letterSpacing: "0.02em",
              color: "var(--color-accent-text)",
            }}
          >
            SCOUTING
          </div>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                padding: "10px 12px",
                borderRadius: "var(--radius-sm)",
                fontSize: 13,
                fontWeight: 600,
                color: isActive ? "var(--color-text)" : "var(--color-text-secondary)",
                background: isActive ? "var(--color-accent-soft)" : "transparent",
                borderLeft: isActive
                  ? "2px solid var(--color-accent)"
                  : "2px solid transparent",
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div style={{ marginTop: "auto", paddingTop: "var(--space-5)" }}>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", lineHeight: 1.6 }}>
            Professional goalkeeper
            <br />
            scouting intelligence.
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, minWidth: 0 }}>
        <div style={{ maxWidth: 1240, margin: "0 auto", padding: "var(--space-6) var(--space-6)" }}>
          {children}
        </div>
      </main>
    </div>
  );
}
