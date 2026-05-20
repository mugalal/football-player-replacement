"use client";
import { X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { PlayerSummary } from "@/lib/types";
import { AVATAR_PALETTE } from "@/lib/constants";
import { cn, fmtNum, initialsFromName, stableIndex } from "@/lib/utils";

interface SourcePlayerHeroProps {
  player: PlayerSummary;
  onRemove: () => void;
}

/**
 * Player-card display for a selected source on /replace.
 *
 * Photo-forward: a full-width square image at the top of the card
 * (rounded top corners that follow the card), with the player's details
 * below. Initials fallback fills the same area with a colored block
 * instead of a small circle.
 */
export function SourcePlayerHero({ player, onRemove }: SourcePlayerHeroProps) {
  const [photoFailed, setPhotoFailed] = useState(false);
  const showPhoto = !!player.photo_url && !photoFailed;
  const initials = initialsFromName(player.name);
  const fallbackColor = AVATAR_PALETTE[stableIndex(player.name, AVATAR_PALETTE.length)];

  return (
    <div className="relative rounded-lg border border-border bg-card overflow-hidden">
      <button
        onClick={onRemove}
        aria-label={`Remove ${player.name}`}
        className="absolute top-2 right-2 z-10 inline-flex h-7 w-7 items-center justify-center rounded-md bg-background/70 backdrop-blur text-foreground hover:bg-background transition-colors"
      >
        <X className="h-4 w-4" />
      </button>

      {/* Photo — square, full card width. Click → player profile. */}
      <Link
        href={`/player/${encodeURIComponent(player.player_id)}`}
        aria-label={`Open ${player.name} profile`}
        className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <div className="relative aspect-square w-full bg-muted">
          {showPhoto ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={player.photo_url ?? ""}
              alt={player.name}
              onError={() => setPhotoFailed(true)}
              className="absolute inset-0 h-full w-full object-cover"
            />
          ) : (
            <div
              className={cn(
                "absolute inset-0 flex items-center justify-center",
                "bg-gradient-to-b from-white/10 to-black/15",
                fallbackColor,
              )}
            >
              <span className="text-6xl font-bold text-white drop-shadow-md select-none">
                {initials}
              </span>
            </div>
          )}
          {/* Subtle gradient overlay at the bottom of the photo so the name
              line below has air to breathe against the divider. */}
          <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-card to-transparent pointer-events-none" />
        </div>
      </Link>

      {/* Detail panel */}
      <div className="p-4 space-y-3">
        <div>
          <Link
            href={`/player/${encodeURIComponent(player.player_id)}`}
            className="text-base font-semibold tracking-tight leading-tight hover:text-primary transition-colors line-clamp-2"
          >
            {player.name}
          </Link>
          <div className="mt-1 text-xs text-muted-foreground">
            {player.primary_position}
          </div>
          <div className="text-xs text-muted-foreground/80">{player.team}</div>
        </div>

        <div className="grid grid-cols-2 gap-2 border-t border-border/60 pt-3">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70">
              Versat.
            </div>
            <div
              className="font-mono text-sm font-semibold tabular-nums"
              data-numeric
            >
              {fmtNum(player.versatility_score, 2)}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70">
              Matches
            </div>
            <div
              className="font-mono text-sm font-semibold tabular-nums"
              data-numeric
            >
              {player.num_matches}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
