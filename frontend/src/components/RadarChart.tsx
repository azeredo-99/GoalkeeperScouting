interface Series {
  name: string;
  color: string;
  values: number[]; // raw metric values, same order as `labels`
}

// Normalização min-max só para desenho do polígono (mesma técnica de
// visuals.plot_radar) -- não é um recálculo de métrica, é só a projeção
// no eixo 0-1 do gráfico.
function normalizeAxis(values: number[]): number[] {
  const finite = values.filter((v) => Number.isFinite(v));
  if (finite.length === 0) return values.map(() => 0);
  const min = Math.min(...finite);
  const max = Math.max(...finite);
  if (max === min) return values.map(() => 0.5);
  return values.map((v) => (Number.isFinite(v) ? (v - min) / (max - min) : 0));
}

export function RadarChart({ labels, series, size = 260 }: { labels: string[]; series: Series[]; size?: number }) {
  const center = size / 2;
  const radius = size / 2 - 40;
  const angleFor = (i: number) => (Math.PI * 2 * i) / labels.length - Math.PI / 2;

  const axesNormalized = labels.map((_, axisIndex) =>
    normalizeAxis(series.map((s) => s.values[axisIndex]))
  );

  const points = (seriesIndex: number) =>
    labels
      .map((_, axisIndex) => {
        const norm = axesNormalized[axisIndex][seriesIndex];
        const r = norm * radius;
        const angle = angleFor(axisIndex);
        return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
      })
      .join(" ");

  return (
    <svg width={size} height={size}>
      {[0.25, 0.5, 0.75, 1].map((ratio) => (
        <polygon
          key={ratio}
          points={labels
            .map((_, i) => {
              const angle = angleFor(i);
              const r = radius * ratio;
              return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
            })
            .join(" ")}
          fill="none"
          stroke="var(--color-border)"
        />
      ))}

      {labels.map((label, i) => {
        const angle = angleFor(i);
        const lx = center + (radius + 22) * Math.cos(angle);
        const ly = center + (radius + 22) * Math.sin(angle);
        return (
          <text
            key={label}
            x={lx}
            y={ly}
            fontSize={10}
            fill="var(--color-text-tertiary)"
            textAnchor="middle"
            dominantBaseline="middle"
          >
            {label}
          </text>
        );
      })}

      {series.map((s, si) => (
        <polygon
          key={s.name}
          points={points(si)}
          fill={s.color}
          fillOpacity={0.14}
          stroke={s.color}
          strokeWidth={1.5}
        />
      ))}
    </svg>
  );
}
