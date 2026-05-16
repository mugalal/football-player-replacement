"use client";
import Link from "next/link";

import { PlayerAvatar } from "@/components/player/PlayerAvatar";
import type { Candidate } from "@/lib/types";
import { cn, fmtNum, fmtPct } from "@/lib/utils";

interface ResultsTableProps {
  candidates: Candidate[];
  showAttackerRank?: boolean;
  highlightName?: string;
}

export function ResultsTable({
  candidates,
  showAttackerRank,
  highlightName,
}: ResultsTableProps) {
  return (
    <div className="rounded-lg border border-border overflow-hidden bg-card">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-muted/30">
          <tr className="text-[10px] uppercase tracking-wider text-muted-foreground">
            <th className="px-4 py-2.5 text-left font-semibold w-12">#</th>
            <th className="px-4 py-2.5 text-left font-semibold">Player</th>
            <th className="px-4 py-2.5 text-left font-semibold hidden md:table-cell">
              Position
            </th>
            <th className="px-4 py-2.5 text-left font-semibold hidden lg:table-cell">
              Team
            </th>
            <th className="px-4 py-2.5 text-right font-semibold w-40">Similarity</th>
            <th className="px-4 py-2.5 text-right font-semibold w-20 hidden sm:table-cell">
              Versat.
            </th>
            <th className="px-4 py-2.5 text-right font-semibold w-16 hidden sm:table-cell">
              Matches
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/60">
          {candidates.map((c) => {
            const rank = showAttackerRank && c.attacker_rank ? c.attacker_rank : c.rank;
            const isHighlighted =
              highlightName && c.name.toLowerCase().includes(highlightName.toLowerCase());
            const isTop = rank === 1;
            return (
              <tr
                key={c.player_id}
                className={cn(
                  "group transition-colors hover:bg-accent/40",
                  isHighlighted && "bg-primary/[0.06] hover:bg-primary/10",
                )}
              >
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      "inline-flex items-center justify-center h-6 min-w-6 px-1.5 rounded text-[11px] font-mono",
                      isTop
                        ? "bg-primary/15 text-primary ring-1 ring-primary/30"
                        : "text-muted-foreground",
                    )}
                    data-numeric
                  >
                    {rank}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/player/${encodeURIComponent(c.player_id)}`}
                    className="flex items-center gap-3 group/link"
                  >
                    <PlayerAvatar
                      photoUrl={c.photo_url}
                      name={c.name}
                      size="sm"
                    />
                    <div className="min-w-0">
                      <div className="font-medium group-hover/link:text-primary transition-colors truncate">
                        {c.name}
                      </div>
                      <div className="text-xs text-muted-foreground md:hidden truncate">
                        {c.primary_position} · {c.team}
                      </div>
                    </div>
                  </Link>
                </td>
                <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">
                  {c.primary_position}
                </td>
                <td className="px-4 py-3 text-muted-foreground hidden lg:table-cell truncate max-w-[160px]">
                  {c.team}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2 justify-end">
                    <div className="h-1.5 w-20 rounded-full bg-secondary overflow-hidden shrink-0">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          isTop ? "bg-primary" : "bg-primary/70",
                        )}
                        style={{ width: `${Math.max(0, Math.min(100, c.similarity * 100))}%` }}
                      />
                    </div>
                    <span
                      className={cn(
                        "font-mono text-xs w-12 text-right tabular-nums",
                        isTop ? "text-foreground font-semibold" : "text-muted-foreground",
                      )}
                      data-numeric
                    >
                      {fmtPct(c.similarity, 1)}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs text-muted-foreground hidden sm:table-cell" data-numeric>
                  {fmtNum(c.versatility_score, 2)}
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs text-muted-foreground hidden sm:table-cell" data-numeric>
                  {c.num_matches}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
