import Link from "next/link";
import { X } from "lucide-react";

import { PlayerAvatar } from "@/components/player/PlayerAvatar";
import type { PlayerSummary } from "@/lib/types";
import { cn, fmtNum } from "@/lib/utils";

interface PlayerCardProps {
  player: PlayerSummary;
  onRemove?: () => void;
  href?: string;
  compact?: boolean;
}

export function PlayerCard({ player, onRemove, href, compact }: PlayerCardProps) {
  const inner = (
    <>
      <PlayerAvatar
        photoUrl={player.photo_url}
        name={player.name}
        size={compact ? "sm" : "md"}
      />
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium truncate leading-tight">{player.name}</div>
        <div className="text-[11px] text-muted-foreground truncate mt-0.5">
          {player.primary_position} · {player.team}
        </div>
      </div>
      <div className="flex flex-col items-end gap-0.5 shrink-0">
        <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground/70" data-numeric>
          v{fmtNum(player.versatility_score, 2)}
        </div>
        <div className="text-[10px] font-mono text-muted-foreground/70" data-numeric>
          {player.num_matches}m
        </div>
      </div>
    </>
  );

  const className = cn(
    "flex items-center gap-3 rounded-md border border-border bg-card/60 p-2.5 transition-colors",
    href && "hover:bg-accent hover:border-primary/30 cursor-pointer",
  );

  return (
    <div className="relative group">
      {href ? (
        <Link href={href} className={className}>
          {inner}
        </Link>
      ) : (
        <div className={className}>{inner}</div>
      )}
      {onRemove && (
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onRemove();
          }}
          aria-label={`Remove ${player.name}`}
          className="absolute -top-1.5 -right-1.5 h-5 w-5 inline-flex items-center justify-center rounded-full bg-background border border-border text-muted-foreground hover:text-destructive hover:border-destructive opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>
  );
}
