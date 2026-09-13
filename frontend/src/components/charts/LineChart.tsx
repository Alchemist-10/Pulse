import { cn } from "@/lib/cn";

// Minimal hand-rolled SVG line chart for the lab/vital trend series. No
// charting library dependency — see BarChart.tsx for the rationale.
//
// Abnormal points are never marked by colour alone: each carries a distinct
// marker shape (a ring instead of a dot) in addition to the critical colour,
// and the caller renders the same points as text rows below the chart with
// an icon + label (.claude/rules/frontend.md, clinical-safety.md — colour
// never carries meaning alone).

export interface LinePoint {
  x: string;
  value: number;
  abnormal: boolean;
}

interface LineChartProps {
  data: LinePoint[];
  ariaLabel: string;
  className?: string;
}

const WIDTH = 480;
const HEIGHT = 160;
const PAD = 24;

export function LineChart({ data, ariaLabel, className }: LineChartProps) {
  if (data.length === 0) return null;

  const values = data.map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = data.map((d, i) => {
    const x = data.length === 1 ? WIDTH / 2 : PAD + (i / (data.length - 1)) * (WIDTH - PAD * 2);
    const y = HEIGHT - PAD - ((d.value - min) / range) * (HEIGHT - PAD * 2);
    return { ...d, x, y };
  });

  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");

  return (
    <div className={cn("w-full overflow-x-auto", className)} role="img" aria-label={ariaLabel}>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        width={WIDTH}
        height={HEIGHT}
        aria-hidden="true"
        className="min-w-full"
      >
        <path d={path} fill="none" stroke="var(--color-accent)" strokeWidth={2} />
        {points.map((p, i) => (
          <g key={i}>
            {p.abnormal ? (
              <circle
                cx={p.x}
                cy={p.y}
                r={6}
                fill="none"
                stroke="var(--color-critical)"
                strokeWidth={2}
              >
                <title>{`${data[i].x}: ${data[i].value}`}</title>
              </circle>
            ) : (
              <circle cx={p.x} cy={p.y} r={3} fill="var(--color-accent)">
                <title>{`${data[i].x}: ${data[i].value}`}</title>
              </circle>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}
