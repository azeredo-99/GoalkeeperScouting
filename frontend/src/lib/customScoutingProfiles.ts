import { useSyncExternalStore } from "react";
import type { ScoutingProfile } from "../api/types";

// Perfis criados/duplicados localmente pelo scout -- mesma arquitetura
// do Shortlist (localStorage + useSyncExternalStore): não há conta,
// não há partilha entre dispositivos nesta fase. Os 3 perfis
// predefinidos continuam a viver no backend (fonte da verdade,
// read-only); um "duplicate" copia a definição para aqui, onde passa
// a ser editável (pesos/mínimos/máximos), sem alterar o original.
const STORAGE_KEY = "gk-scouting.custom-profiles.v1";

function readStorage(): ScoutingProfile[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

let profiles: ScoutingProfile[] = readStorage();
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profiles));
  } catch {
    // localStorage indisponível -- os perfis personalizados simplesmente
    // não sobrevivem a um refresh; não é fatal.
  }
}

export function getCustomProfiles(): ScoutingProfile[] {
  return profiles;
}

export function duplicateProfile(base: ScoutingProfile): ScoutingProfile {
  const copy: ScoutingProfile = {
    ...base,
    id: `custom-${Date.now()}`,
    name: `${base.name} (copy)`,
    preferences: base.preferences.map((p) => ({ ...p })),
  };
  profiles = [...profiles, copy];
  persist();
  emit();
  return copy;
}

export function updateProfilePreference(
  profileId: string,
  metric: string,
  patch: Partial<{ enabled: boolean; weight: number; minimum: number | null; maximum: number | null }>
): void {
  profiles = profiles.map((p) =>
    p.id !== profileId
      ? p
      : { ...p, preferences: p.preferences.map((pref) => (pref.metric === metric ? { ...pref, ...patch } : pref)) }
  );
  persist();
  emit();
}

export function removeCustomProfile(profileId: string): void {
  profiles = profiles.filter((p) => p.id !== profileId);
  persist();
  emit();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useCustomProfiles(): ScoutingProfile[] {
  return useSyncExternalStore(subscribe, getCustomProfiles, getCustomProfiles);
}
