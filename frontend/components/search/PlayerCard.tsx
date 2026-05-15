import Link from "next/link";

import { PlayerAvatar } from "@/components/player/PlayerAvatar";
import type { PlayerSummary } from "@/lib/types";
import { fmtNum } from "@/lib/utils";

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
        <div className="text-sm font-medium truncate">{player.name}</div>
        <div className="text-xs text-muted-foreground truncate">
          {player.primary_position} · {player.team}
        </div>
      </div>
      <div className="text-xs font-mono text-muted-foreground shrink-0" data-numeric>
        v {fmtNum(player.versatility_score, 2)}
        <span className="mx-1">·</span>
        {player.num_matches}m
      </div>
    </>
  );

  const className = `flex items-center gap-3 rounded-md border border-border bg-card p-2.5 ${
    href ? "hover:bg-accent transition-colors cursor-pointer" : ""
  }`;

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
          className="absolute -top-2 -right-2 h-5 w-5 rounded-full bg-background border border-border text-xs font-bold text-muted-foreground hover:text-destructive hover:border-destructive opacity-0 group-hover:opacity-100 transition-opacity"
        >
          ×
        </button>
      )}
    </div>
  );
}
