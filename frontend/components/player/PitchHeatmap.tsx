/**
 * PitchHeatmap — SVG football pitch with a 6×3 zone heat overlay.
 *
 * Renders a StatsBomb-style 120×80 pitch with standard markings (penalty
 * areas, six-yard boxes, goals, halfway line, centre circle) and overlays
 * a 6×3 grid of heat-tinted rectangles, intensity proportional to the
 * supplied per-zone counts.
 *
 * Direction: attacking left-to-right (zone 0 is the defensive top-left
 * corner, zone 17 is the attacking bottom-right). This matches the
 * StatsBomb coordinate system used by src/gp2/preprocess/zones.py.
 *
 * Color: a single primary-tinted ramp; we use rgba with the page primary
 * hue so the component looks right in both light and dark themes.
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
const PAD = 4; // SVG padding around the pitch outline

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

      <div className="rounded-md border border-border bg-card/60 p-3">
        <svg
          viewBox={`${-PAD} ${-PAD} ${PITCH_W + 2 * PAD} ${PITCH_H + 2 * PAD}`}
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto"
          aria-label={title ?? "Pitch heatmap"}
        >
          {/* Pitch background (the green) */}
          <rect
            x="0"
            y="0"
            width={PITCH_W}
            height={PITCH_H}
            className="fill-emerald-900/15 dark:fill-emerald-900/20"
            stroke="currentColor"
            strokeOpacity="0.35"
            strokeWidth="0.4"
          />

          {/* Heat overlay cells — drawn UNDER the pitch lines so markings stay legible */}
          {safeCounts.map((c, i) => {
            const bx = i % numX;
            const by = Math.floor(i / numX);
            const intensity = c / maxCount; // 0..1
            // Smooth ramp; cap at 0.85 so darkest cells still show pitch lines through.
            const alpha = c === 0 ? 0 : 0.1 + 0.75 * intensity;
            return (
              <rect
                key={i}
                x={bx * cellW}
                y={by * cellH}
                width={cellW}
                height={cellH}
                className="fill-primary"
                style={{ fillOpacity: alpha }}
              />
            );
          })}

          {/* Pitch markings (drawn on top of the heat) */}
          <g
            stroke="currentColor"
            strokeOpacity="0.55"
            strokeWidth="0.4"
            fill="none"
          >
            {/* Outer rectangle is already drawn above */}
            {/* Halfway line */}
            <line x1={PITCH_W / 2} y1="0" x2={PITCH_W / 2} y2={PITCH_H} />
            {/* Centre circle (10 yards = ~9.15m, scaled to pitch units) */}
            <circle cx={PITCH_W / 2} cy={PITCH_H / 2} r="9.15" />
            <circle cx={PITCH_W / 2} cy={PITCH_H / 2} r="0.6" fill="currentColor" fillOpacity="0.7" />

            {/* Left penalty area (18 yards × 44 yards) */}
            <rect x="0" y={(PITCH_H - 44) / 2} width="18" height="44" />
            {/* Left 6-yard box */}
            <rect x="0" y={(PITCH_H - 20) / 2} width="6" height="20" />
            {/* Left penalty spot */}
            <circle cx="12" cy={PITCH_H / 2} r="0.6" fill="currentColor" fillOpacity="0.7" />

            {/* Right penalty area */}
            <rect x={PITCH_W - 18} y={(PITCH_H - 44) / 2} width="18" height="44" />
            {/* Right 6-yard box */}
            <rect x={PITCH_W - 6} y={(PITCH_H - 20) / 2} width="6" height="20" />
            {/* Right penalty spot */}
            <circle cx={PITCH_W - 12} cy={PITCH_H / 2} r="0.6" fill="currentColor" fillOpacity="0.7" />

            {/* Goals (small protrusions outside the pitch line) */}
            <rect x="-1.5" y={(PITCH_H - 8) / 2} width="1.5" height="8" />
            <rect x={PITCH_W} y={(PITCH_H - 8) / 2} width="1.5" height="8" />
          </g>

          {/* Tiny direction-of-attack arrow at the bottom edge */}
          <g
            transform={`translate(${PITCH_W / 2 - 6}, ${PITCH_H + 2.5})`}
            className="text-muted-foreground"
            fill="currentColor"
            opacity="0.7"
          >
            <line x1="0" y1="0" x2="10" y2="0" stroke="currentColor" strokeWidth="0.5" />
            <polygon points="10,0 8,-1.2 8,1.2" />
          </g>
        </svg>
      </div>
    </div>
  );
}
