import type { PerformanceRow } from "../api/types";

// O Discovery representa o guarda-redes como entidade, não como uma
// linha de performance -- um jogador com várias competições/épocas
// aparece uma única vez, com a amostra de mais minutos como
// representativa. Os outros contextos não desaparecem: continuam
// disponíveis no Profile, só não duplicam o resultado aqui.
export interface PlayerEntity {
  playerName: string;
  primary: PerformanceRow;
  contexts: PerformanceRow[];
}

export function pickPrimaryContext(rows: PerformanceRow[]): PerformanceRow {
  return [...rows].sort((a, b) => (b.minutes ?? 0) - (a.minutes ?? 0))[0];
}

export function groupByPlayer(rows: PerformanceRow[]): PlayerEntity[] {
  const order: string[] = [];
  const map = new Map<string, PerformanceRow[]>();
  for (const row of rows) {
    if (!map.has(row.playerName)) {
      order.push(row.playerName);
      map.set(row.playerName, []);
    }
    map.get(row.playerName)!.push(row);
  }
  return order.map((playerName) => {
    const contexts = map.get(playerName)!;
    return { playerName, primary: pickPrimaryContext(contexts), contexts };
  });
}
