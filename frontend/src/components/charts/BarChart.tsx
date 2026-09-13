import { cn } from "@/lib/cn";

// Minimal hand-rolled SVG bar chart. No charting library dependency: the
// series here (visit-frequency-by-month, provider-entry-counts) are small,
// static, single-series bar shapes with no need for pan/zoom/legend
// interactivity, so a library's bundle weight and API surface bought nothing
// (academic project, smaller footprint preferred).
//
// Colour comes only from design tokens (`var(--color-*)`), never a hex
// literal (ESLint: no hex under src/components/). Bars also carry a
// `<title>` tooltip and each value is present as visible text via the
// caller's own list/table rendering — the chart is a visual summary, not the
// only place the data appears.

export interface BarDatum {
  label: string;
  value: number;
}

interface BarChartProps {
  data: BarDatum[];
  /** Accessible label for the whole chart (e.g. "Visits per month"). */
  ariaLabel: string;
  formatValue?: (value: number) => string;
  className?: string;
}

const HEIGHT = 160;
const BAR_GAP = 8;

export function BarChart({ data, ariaLabel, formatValue, className }: BarChartProps) {
  const max = Math.max(1, ...data.map((d) => d.value));
  const fmt = formatValue ?? ((v: number) => String(v));

  return (
    <div className={cn("w-full overflow-x-auto", className)} role="img" aria-label={ariaLabel}>
      <svg
        viewBox={`0 0 ${data.length * 48} ${HEIGHT}`}
        width={Math.max(data.length * 48, 240)}
        height={HEIGHT}
        aria-hidden="true"
        className="min-w-full"
      >
        <line
          x1="0"
          y1={HEIGHT - 20}
          x2={data.length * 48}
          y2={HEIGHT - 20}
          stroke="var(--color-border)"
          strokeWidth={1}
        />
        {data.map((d, i) => {
          const barHeight = Math.round(((HEIGHT - 32) * d.value) / max);
          const x = i * 48 + BAR_GAP;
          const y = HEIGHT - 20 - barHeight;
          return (
            <g key={`${d.label}-${i}`}>
              <rect
                x={x}
                y={y}
                width={48 - BAR_GAP * 2}
                height={barHeight}
                rx={3}
                fill="var(--color-accent)"
              >
                <title>{`${d.label}: ${fmt(d.value)}`}</title>
              </rect>
              <text
                x={x + (48 - BAR_GAP * 2) / 2}
                y={HEIGHT - 6}
                textAnchor="middle"
                fontSize={10}
                fill="var(--color-muted)"
              >
                {d.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
