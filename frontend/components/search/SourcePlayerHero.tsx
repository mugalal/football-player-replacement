"use client";
import { X } from "lucide-react";
import Link from "next/link";

import { PlayerAvatar } from "@/components/player/PlayerAvatar";
import type { PlayerSummary } from "@/lib/types";
import { fmtNum } from "@/lib/utils";

interface SourcePlayerHeroProps {
  player: PlayerSummary;
  onRemove: () => void;
}

/**
 * Large, prominent display for a selected source player on /replace.
 *
 * Uses the 2xl avatar size (176×176) so the photo is visible at a glance.
 * Detail row underneath shows position, team, and the numeric facts the
 * user might want to sanity-check before searching.
 */
export function SourcePlayerHero({ player, onRemove }: SourcePlayerHeroProps) {
  return (
    <div className="relative rounded-lg border border-border bg-gradient-to-br from-card to-card/60 p-5 overflow-hidden">
      <button
        onClick={onRemove}
        aria-label={`Remove ${player.name}`}
        className="absolute top-2 right-2 inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex flex-col items-center text-center">
        <Link
          href={`/player/${encodeURIComponent(player.player_id)}`}
          className="block focus:outline-none rounded-full"
          aria-label={`Open ${player.name} profile`}
        >
          <PlayerAvatar
            photoUrl={player.photo_url}
            name={player.name}
            size="2xl"
            className="ring-2 ring-primary/40 shadow-lg"
          />
        </Link>
        <h3 className="mt-4 text-base font-semibold tracking-tight leading-tight">
          {player.name}
        </h3>
        <p className="mt-1 text-xs text-muted-foreground">
          {player.primary_position}
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground/80">{player.team}</p>

        <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
          <div className="text-right">
            <div className="font-mono font-medium text-foreground tabular-nums" data-numeric>
              {fmtNum(player.versatility_score, 2)}
            </div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70">
              Versat.
            </div>
          </div>
          <div className="text-left">
            <div className="font-mono font-medium text-foreground tabular-nums" data-numeric>
              {player.num_matches}
            </div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70">
              Matches
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
