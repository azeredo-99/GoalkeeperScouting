import { useSyncExternalStore } from "react";

// O shortlist representa o GUARDA-REDES, não uma linha de performance --
// um jogador com várias competições/épocas continua a aparecer uma
// única vez (ver lib/players.groupByPlayer, o mesmo princípio usado no
// Discovery). O contexto guardado é só a amostra "atual" para
// apresentação; identidade == playerName.
//
// Persistência local (localStorage) por desenho -- esta fase é
// deliberadamente client-side. A forma dos dados foi escolhida para
// poder vir a ser espelhada num endpoint de backend mais tarde sem
// alterar a forma como o resto da app consome o shortlist (só a
// implementação de leitura/escrita mudaria). Nunca guarda métricas --
// isso continua a vir sempre da API, nunca duplicado aqui.
export type Priority = "normal" | "high" | "priority";
export type ScoutingStatus = "watch" | "reviewing" | "target" | "passed";

export const PRIORITY_LABELS: Record<Priority, string> = {
  normal: "Normal",
  high: "High",
  priority: "Priority",
};

export const STATUS_LABELS: Record<ScoutingStatus, string> = {
  watch: "Watch",
  reviewing: "Reviewing",
  target: "Target",
  passed: "Passed",
};

export interface ShortlistEntry {
  playerName: string;
  competitionId: number;
  seasonId: number;
  priority: Priority;
  status: ScoutingStatus;
  note: string;
  createdAt: number;
}

const STORAGE_KEY = "gk-scouting.shortlist.v1";

// v1 original só tinha {playerName, competitionId, seasonId}. Ler dados
// antigos e completar os campos novos com valores neutros por omissão --
// nunca descarta um jogador só porque foi guardado antes desta fase.
function migrateEntry(raw: unknown): ShortlistEntry | null {
  if (!raw || typeof raw !== "object") return null;
  const e = raw as Record<string, unknown>;
  if (typeof e.playerName !== "string" || typeof e.competitionId !== "number" || typeof e.seasonId !== "number") {
    return null;
  }
  const priority: Priority =
    e.priority === "high" || e.priority === "priority" ? e.priority : "normal";
  const status: ScoutingStatus =
    e.status === "reviewing" || e.status === "target" || e.status === "passed" ? e.status : "watch";
  return {
    playerName: e.playerName,
    competitionId: e.competitionId,
    seasonId: e.seasonId,
    priority,
    status,
    note: typeof e.note === "string" ? e.note : "",
    createdAt: typeof e.createdAt === "number" ? e.createdAt : Date.now(),
  };
}

function readStorage(): ShortlistEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map(migrateEntry).filter((e): e is ShortlistEntry => e !== null);
  } catch {
    return [];
  }
}

let entries: ShortlistEntry[] = readStorage();
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // localStorage indisponível (modo privado, quota excedida, etc.) --
    // o shortlist simplesmente não sobrevive a um refresh; não é fatal.
  }
}

export function getShortlist(): ShortlistEntry[] {
  return entries;
}

export function isShortlisted(playerName: string): boolean {
  return entries.some((e) => e.playerName === playerName);
}

export function addToShortlist(playerName: string, competitionId: number, seasonId: number): void {
  if (isShortlisted(playerName)) return;
  entries = [
    ...entries,
    { playerName, competitionId, seasonId, priority: "normal", status: "watch", note: "", createdAt: Date.now() },
  ];
  persist();
  emit();
}

export function removeFromShortlist(playerName: string): void {
  if (!isShortlisted(playerName)) return;
  entries = entries.filter((e) => e.playerName !== playerName);
  persist();
  emit();
}

function updateEntry(playerName: string, patch: Partial<ShortlistEntry>): void {
  const index = entries.findIndex((e) => e.playerName === playerName);
  if (index === -1) return;
  entries = entries.map((e, i) => (i === index ? { ...e, ...patch } : e));
  persist();
  emit();
}

export function setPriority(playerName: string, priority: Priority): void {
  updateEntry(playerName, { priority });
}

export function setStatus(playerName: string, status: ScoutingStatus): void {
  updateEntry(playerName, { status });
}

export function setNote(playerName: string, note: string): void {
  updateEntry(playerName, { note });
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useShortlist(): ShortlistEntry[] {
  return useSyncExternalStore(subscribe, getShortlist, getShortlist);
}

export function useIsShortlisted(playerName: string): boolean {
  const list = useShortlist();
  return list.some((e) => e.playerName === playerName);
}
