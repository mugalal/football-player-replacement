"use client";
import Link from "next/link";

import { PlayerAvatar } from "@/components/player/PlayerAvatar";
import type { Candidate } from "@/lib/types";
import { cn, fmtPct } from "@/lib/utils";

interface CandidatePodiumProps {
  candidates: Candidate[];
  highlightName?: string;
}

/**
 * Top-3 candidates as big photo-forward cards.
 *
 * Sits above the dense results table. Rank #1 is highlighted in the
 * primary tone (gold/green). Each card links to /player/[id].
 *
 * If fewer than 3 candidates exist, the grid still renders evenly.
 */
export function CandidatePodium({ candidates, highlightName }: CandidatePodiumProps) {
  const top = candidates.slice(0, 3);
  if (top.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
      {top.map((c) => {
        const isTop = c.rank === 1;
        const isHighlighted =
          highlightName && c.name.toLowerCase().includes(highlightName.toLowerCase());
        return (
          <Link
            key={c.player_id}
            href={`/player/${encodeURIComponent(c.player_id)}`}
            className={cn(
              "group relative flex flex-col items-center text-center rounded-lg border bg-card p-5 transition-all hover:bg-card/80",
              isTop
                ? "border-primary/50 bg-primary/[0.04] hover:bg-primary/10"
                : "border-border",
              isHighlighted && !isTop && "border-primary/40 bg-primary/[0.03]",
            )}
          >
            {/* Rank chip top-left */}
            <span
              className={cn(
                "absolute top-3 left-3 inline-flex items-center justify-center h-7 min-w-7 px-1.5 rounded text-xs font-mono",
                isTop
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground",
              )}
              data-numeric
            >
              #{c.rank}
            </span>

            {/* Similarity top-right */}
            <span
              className={cn(
                "absolute top-3 right-3 font-mono text-sm tabular-nums",
                isTop ? "text-primary font-semibold" : "text-foreground",
              )}
              data-numeric
            >
              {fmtPct(c.similarity, 1)}
            </span>

            {/* Photo */}
            <PlayerAvatar
              photoUrl={c.photo_url}
              name={c.name}
              size={isTop ? "2xl" : "xl"}
              className={cn(
                "mt-6 shadow-lg",
                isTop ? "ring-2 ring-primary/40" : "ring-1 ring-border",
              )}
            />

            {/* Name + meta */}
            <div className="mt-4 w-full px-1">
              <div
                className={cn(
                  "text-sm font-semibold tracking-tight leading-tight line-clamp-2 min-h-[2.5rem]",
                  isTop && "text-foreground",
                )}
              >
                {c.name}
              </div>
              <div className="mt-1 text-[11px] text-muted-foreground truncate">
                {c.primary_position}
              </div>
              <div className="text-[11px] text-muted-foreground/80 truncate">
                {c.team}
              </div>
            </div>

            {/* Similarity bar at the bottom */}
            <div className="mt-3 w-full h-1 rounded-full bg-secondary overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  isTop ? "bg-primary" : "bg-primary/60",
                )}
                style={{
                  width: `${Math.max(0, Math.min(100, c.similarity * 100))}%`,
                }}
              />
            </div>
          </Link>
        );
      })}
    </div>
  );
}
