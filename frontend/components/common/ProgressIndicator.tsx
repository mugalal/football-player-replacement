import { Loader2 } from "lucide-react";

interface ProgressIndicatorProps {
  message: string;
  elapsedMs: number;
}

export function ProgressIndicator({ message, elapsedMs }: ProgressIndicatorProps) {
  const seconds = Math.floor(elapsedMs / 1000);
  return (
    <div className="rounded-md border border-border bg-card p-4 flex items-center gap-3">
      <Loader2 className="h-4 w-4 animate-spin text-primary" aria-hidden />
      <div className="flex-1">
        <p className="text-sm font-medium">{message}</p>
        <p className="text-xs text-muted-foreground font-mono mt-0.5">
          {seconds}s elapsed · typically 30–60s with upgrades
        </p>
      </div>
    </div>
  );
}
