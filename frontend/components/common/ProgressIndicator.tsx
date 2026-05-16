import { Loader2 } from "lucide-react";

interface ProgressIndicatorProps {
  message: string;
  elapsedMs: number;
}

export function ProgressIndicator({ message, elapsedMs }: ProgressIndicatorProps) {
  const seconds = Math.floor(elapsedMs / 1000);
  return (
    <div className="rounded-lg border border-primary/30 bg-primary/5 p-5">
      <div className="flex items-start gap-3">
        <Loader2 className="h-5 w-5 animate-spin text-primary mt-0.5 shrink-0" aria-hidden />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{message}</p>
          <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
            Per-match Doc2Vec inference + 10× repetition smoothing per source player.
            Typically 30–60s.
          </p>
        </div>
        <div className="text-right shrink-0">
          <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
            Elapsed
          </div>
          <div className="text-2xl font-mono font-semibold text-primary tabular-nums" data-numeric>
            {seconds}s
          </div>
        </div>
      </div>
    </div>
  );
}
