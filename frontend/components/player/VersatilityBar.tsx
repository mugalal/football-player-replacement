import { cn, fmtNum } from "@/lib/utils";

interface VersatilityBarProps {
  score: number;
  /** Practical scale: engine emits Shannon entropy; observed range is 0–2.5. */
  max?: number;
  className?: string;
}

export function VersatilityBar({ score, max = 2.5, className }: VersatilityBarProps) {
  const pct = Math.max(0, Math.min(100, (score / max) * 100));
  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Versatility</span>
        <span className="font-mono" data-numeric>
          {fmtNum(score, 3)}
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
        <div
          className="h-full bg-primary transition-[width] duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
