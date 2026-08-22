// Placeholder honesto -- não há dados de localização de eventos
// disponíveis em lado nenhum do pipeline (avgDistanceFromGoal/
// maxDistanceFromGoal são escalares, não coordenadas), por isso o mapa
// nunca teve nem pode ter uma versão "com dados": mostra sempre este
// aviso. Extraído para partilhar exatamente o mesmo texto/estilo entre
// o Player Profile e o Scouting Report.
export function SweeperMap({ height = 180 }: { height?: number }) {
  return (
    <div
      style={{
        height,
        borderRadius: "var(--radius-md)",
        border: "1px dashed var(--color-border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--color-text-tertiary)",
        fontSize: 13,
        textAlign: "center",
        padding: "var(--space-4)",
      }}
    >
      Shot/location data unavailable for this sample.
    </div>
  );
}
