/**
 * PitchHeatmap — SVG football pitch with a smoothed zone heat overlay.
 *
 * The engine bins actions to a 6×3 zone grid (src/gp2/preprocess/zones.py),
 * so the underlying data is 18 numbers per player. We render those zones
 * as discrete colored rectangles, then apply an SVG Gaussian blur filter
 * to produce a Sofascore-style smooth gradient — the visual is continuous
 * even though the source is coarse. Color ramp is the standard sports-
 * heatmap yellow→orange→red applied via a per-cell HSL/RGBA computation.
 *
 * Honesty note: the smoothness is *visual interpolation*, not finer-grain
 * data. We don't have per-action coordinates — only the 18-zone aggregate.
 *
 * Direction: attacking left-to-right (zone 0 is the defensive top-left
 * corner, zone 17 is the attacking bottom-right). This matches the
 * StatsBomb coordinate system used by src/gp2/preprocess/zones.py.
 */
import { cn } from "@/lib/utils";

interface PitchHeatmapProps {
  counts: number[];        // length 18, row-major from top-left
  numX?: number;           // default 6
  numY?: number;           // default 3
  total?: number;          // for the footer label; defaults to sum(counts)
  title?: string;
  subtitle?: string;
  className?: string;
}

// Pitch coordinates match StatsBomb: 120 long × 80 wide.
const PITCH_W = 120;
const PITCH_H = 80;
const PAD = 4;

/**
 * Map a 0..1 intensity to an HSL color along a yellow→orange→red ramp.
 * Below the threshold returns null (cell stays transparent).
 */
function heatColor(intensity: number): string | null {
  if (intensity <= 0.04) return null;
  // Hue: 55° (yellow) → 0° (red). Saturation always high, lightness drops a touch at the hot end.
  const hue = 55 - 55 * intensity;
  const lightness = 60 - 15 * intensity;
  // Alpha rises with intensity so cold tints don't pollute the pitch background.
  const alpha = 0.35 + 0.55 * intensity;
  return `hsla(${hue.toFixed(0)}, 95%, ${lightness.toFixed(0)}%, ${alpha.toFixed(2)})`;
}

export function PitchHeatmap({
  counts,
  numX = 6,
  numY = 3,
  total,
  title,
  subtitle,
  className,
}: PitchHeatmapProps) {
  const safeCounts = counts.length === numX * numY ? counts : new Array(numX * numY).fill(0);
  const maxCount = Math.max(1, ...safeCounts);
  const sumCounts = total ?? safeCounts.reduce((a, b) => a + b, 0);

  const cellW = PITCH_W / numX;
  const cellH = PITCH_H / numY;

  // Unique filter ID so multiple heatmaps on the same page don't collide.
  const filterId = `heat-blur-${title?.replace(/[^a-z0-9]/gi, "") || "h"}-${numX}x${numY}`;

  return (
    <div className={cn("space-y-2", className)}>
      {(title || subtitle) && (
        <div className="flex items-baseline justify-between gap-2 flex-wrap">
          <div>
            {title && <h4 className="text-sm font-semibold tracking-tight">{title}</h4>}
            {subtitle && (
              <p className="text-[11px] text-muted-foreground mt-0.5">{subtitle}</p>
            )}
          </div>
          {sumCounts > 0 && (
            <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground" data-numeric>
              {sumCounts.toLocaleString()} actions
            </span>
          )}
        </div>
      )}

      <div className="rounded-md border border-border bg-[#0f1d12] dark:bg-[#0a1610] p-3 overflow-hidden">
        <svg
          viewBox={`${-PAD} ${-PAD - 4} ${PITCH_W + 2 * PAD} ${PITCH_H + 2 * PAD + 4}`}
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto"
          aria-label={title ?? "Pitch heatmap"}
        >
          <defs>
            {/* Gaussian blur on the heat layer produces the Sofascore-style
                continuous gradient from our discrete 18 cells. stdDeviation
                tuned to roughly span half a cell — strong enough to soften
                cell boundaries, weak enough to keep hot spots localized. */}
            <filter id={filterId} x="-10%" y="-10%" width="120%" height="120%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="6" />
            </filter>
          </defs>

          {/* Direction-of-attack arrow at the TOP edge (matches Sofascore convention) */}
          <g
            transform={`translate(${PITCH_W / 2 - 6}, -1.5)`}
            fill="white"
            fillOpacity="0.5"
          >
            <line x1="0" y1="0" x2="10" y2="0" stroke="white" strokeOpacity="0.5" strokeWidth="0.5" />
            <polygon points="10,0 8,-1.4 8,1.4" />
          </g>

          {/* Pitch background — dark green like Sofascore */}
          <rect
            x="0"
            y="0"
            width={PITCH_W}
            height={PITCH_H}
            fill="#1a3320"
            stroke="white"
            strokeOpacity="0.35"
            strokeWidth="0.4"
          />

          {/* Heat overlay — blurred for the smooth continuous look */}
          <g filter={`url(#${filterId})`}>
            {safeCounts.map((c, i) => {
              const bx = i % numX;
              const by = Math.floor(i / numX);
              const intensity = c / maxCount;
              const color = heatColor(intensity);
              if (!color) return null;
              return (
                <rect
                  key={i}
                  x={bx * cellW}
                  y={by * cellH}
                  width={cellW}
                  height={cellH}
                  fill={color}
                />
              );
            })}
          </g>

          {/* Pitch markings drawn over the heat layer so lines stay sharp */}
          <g
            stroke="white"
            strokeOpacity="0.5"
            strokeWidth="0.4"
            fill="none"
          >
            <line x1={PITCH_W / 2} y1="0" x2={PITCH_W / 2} y2={PITCH_H} />
            <circle cx={PITCH_W / 2} cy={PITCH_H / 2} r="9.15" />
            <circle cx={PITCH_W / 2} cy={PITCH_H / 2} r="0.6" fill="white" fillOpacity="0.65" />

            {/* Left penalty area */}
            <rect x="0" y={(PITCH_H - 44) / 2} width="18" height="44" />
            <rect x="0" y={(PITCH_H - 20) / 2} width="6" height="20" />
            <circle cx="12" cy={PITCH_H / 2} r="0.6" fill="white" fillOpacity="0.65" />

            {/* Right penalty area */}
            <rect x={PITCH_W - 18} y={(PITCH_H - 44) / 2} width="18" height="44" />
            <rect x={PITCH_W - 6} y={(PITCH_H - 20) / 2} width="6" height="20" />
            <circle cx={PITCH_W - 12} cy={PITCH_H / 2} r="0.6" fill="white" fillOpacity="0.65" />

            {/* Goals */}
            <rect x="-1.5" y={(PITCH_H - 8) / 2} width="1.5" height="8" />
            <rect x={PITCH_W} y={(PITCH_H - 8) / 2} width="1.5" height="8" />
          </g>
        </svg>
      </div>
    </div>
  );
}
