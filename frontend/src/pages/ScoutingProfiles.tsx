import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getScoutingProfiles } from "../api/client";
import type { ScoutingProfile } from "../api/types";
import { ErrorState, LoadingState } from "../components/States";
import {
  duplicateProfile,
  removeCustomProfile,
  updateProfilePreference,
  useCustomProfiles,
} from "../lib/customScoutingProfiles";

// Um Scouting Profile é uma predefinição do scout ("o que estou a
// procurar"), nunca uma classificação objetiva do jogador -- por isso
// cada cartão diz isso explicitamente, e as preferências nunca se
// resumem a um único número aqui.
export function ScoutingProfiles() {
  const navigate = useNavigate();
  const [builtIn, setBuiltIn] = useState<ScoutingProfile[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const custom = useCustomProfiles();

  function load() {
    setLoading(true);
    setError(null);
    getScoutingProfiles()
      .then((res) => setBuiltIn(res.profiles))
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  return (
    <div>
      <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 4px" }}>Scouting Profiles</h1>
      <p style={{ color: "var(--color-text-secondary)", margin: "0 0 var(--space-6)" }}>
        Templates of what a scout is looking for — not player ratings. Scout-defined preferences.
      </p>

      {loading && <LoadingState label="Loading scouting profiles…" />}
      {error && <ErrorState message={error} onRetry={load} />}

      {!loading && !error && builtIn && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          {builtIn.map((profile) => (
            <ProfileCard
              key={profile.id}
              profile={profile}
              editable={false}
              onUse={() => navigate(`/discover?scouting_profile=${encodeURIComponent(profile.id)}`)}
              onDuplicate={() => duplicateProfile(profile)}
            />
          ))}
          {custom.map((profile) => (
            <ProfileCard
              key={profile.id}
              profile={profile}
              editable
              onUse={() => navigate(`/discover?scouting_profile=${encodeURIComponent(profile.id)}`)}
              onRemove={() => removeCustomProfile(profile.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ProfileCard({
  profile,
  editable,
  onUse,
  onDuplicate,
  onRemove,
}: {
  profile: ScoutingProfile;
  editable: boolean;
  onUse: () => void;
  onDuplicate?: () => void;
  onRemove?: () => void;
}) {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-4)", flexWrap: "wrap" }}>
        <div>
          <div className="label" style={{ marginBottom: 4 }}>
            {editable ? "Custom scouting profile" : "Scouting profile"}
          </div>
          <div style={{ fontSize: 17, fontWeight: 700 }}>{profile.name}</div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary)", marginTop: 4, maxWidth: 520 }}>
            {profile.description}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={onUse} style={btnPrimary}>
            Use profile
          </button>
          {onDuplicate && (
            <button onClick={onDuplicate} style={btnSecondary}>
              Duplicate
            </button>
          )}
          {onRemove && (
            <button onClick={onRemove} style={btnSecondary}>
              Remove
            </button>
          )}
        </div>
      </div>

      <div style={{ marginTop: "var(--space-4)" }}>
        <div className="label" style={{ marginBottom: 6 }}>
          Scout-defined preferences
        </div>
        <div className="scroll-x">
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr>
                <th style={thStyle}>Metric</th>
                <th style={thStyle}>Enabled</th>
                <th style={thStyle}>Weight</th>
                <th style={thStyle}>Minimum</th>
                <th style={thStyle}>Maximum</th>
              </tr>
            </thead>
            <tbody>
              {profile.preferences.map((pref) => (
                <tr key={pref.metric}>
                  <td style={tdStyle}>{pref.label}</td>
                  <td style={tdStyle}>
                    {editable ? (
                      <input
                        type="checkbox"
                        checked={pref.enabled}
                        onChange={(e) => updateProfilePreference(profile.id, pref.metric, { enabled: e.target.checked })}
                      />
                    ) : (
                      pref.enabled ? "Yes" : "—"
                    )}
                  </td>
                  <td className="tabular" style={tdStyle}>
                    {editable ? (
                      <input
                        type="number"
                        step="0.5"
                        value={pref.weight}
                        onChange={(e) => updateProfilePreference(profile.id, pref.metric, { weight: Number(e.target.value) })}
                        style={numInput}
                      />
                    ) : (
                      pref.enabled ? pref.weight : "—"
                    )}
                  </td>
                  <td className="tabular" style={tdStyle}>
                    {editable ? (
                      <input
                        type="number"
                        value={pref.minimum ?? ""}
                        onChange={(e) =>
                          updateProfilePreference(profile.id, pref.metric, {
                            minimum: e.target.value === "" ? null : Number(e.target.value),
                          })
                        }
                        style={numInput}
                      />
                    ) : (
                      pref.minimum ?? "—"
                    )}
                  </td>
                  <td className="tabular" style={tdStyle}>
                    {editable ? (
                      <input
                        type="number"
                        value={pref.maximum ?? ""}
                        onChange={(e) =>
                          updateProfilePreference(profile.id, pref.metric, {
                            maximum: e.target.value === "" ? null : Number(e.target.value),
                          })
                        }
                        style={numInput}
                      />
                    ) : (
                      pref.maximum ?? "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {editable && (
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 8 }}>
            Custom profiles are usable for reference here; live Discover matching currently supports the built-in profiles only.
          </div>
        )}
      </div>
    </div>
  );
}

const thStyle: CSSProperties = {
  textAlign: "left",
  padding: "6px 10px",
  borderBottom: "1px solid var(--color-border)",
  color: "var(--color-text-secondary)",
  fontWeight: 600,
};

const tdStyle: CSSProperties = {
  padding: "6px 10px",
  borderBottom: "1px solid var(--color-border-soft)",
  fontWeight: 600,
};

const numInput: CSSProperties = {
  width: 70,
  padding: "4px 6px",
  fontSize: 12,
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface-raised)",
  color: "var(--color-text)",
};

const btnBase: CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  borderRadius: "var(--radius-sm)",
  padding: "8px 14px",
  cursor: "pointer",
  border: "1px solid var(--color-border)",
  background: "transparent",
  color: "var(--color-text-secondary)",
};

const btnPrimary: CSSProperties = {
  ...btnBase,
  background: "var(--color-accent)",
  borderColor: "var(--color-accent)",
  color: "#04150e",
};

const btnSecondary: CSSProperties = { ...btnBase };
