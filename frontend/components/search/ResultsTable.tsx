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
    <div className="rounded-md border border-border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="px-3 py-2 text-left font-medium w-12">#</th>
            <th className="px-3 py-2 text-left font-medium">Player</th>
            <th className="px-3 py-2 text-left font-medium hidden md:table-cell">
              Position
            </th>
            <th className="px-3 py-2 text-left font-medium hidden lg:table-cell">
              Team
            </th>
            <th className="px-3 py-2 text-right font-medium w-32">Similarity</th>
            <th className="px-3 py-2 text-right font-medium w-20 hidden sm:table-cell">
              Versatility
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {candidates.map((c) => {
            const rank = showAttackerRank && c.attacker_rank ? c.attacker_rank : c.rank;
            const isHighlighted =
              highlightName && c.name.toLowerCase().includes(highlightName.toLowerCase());
            return (
              <tr
                key={c.player_id}
                className={cn(
                  "transition-colors hover:bg-accent",
                  isHighlighted && "bg-primary/5",
                )}
              >
                <td className="px-3 py-2 font-mono text-muted-foreground" data-numeric>
                  {rank}
                </td>
                <td className="px-3 py-2">
                  <Link
                    href={`/player/${encodeURIComponent(c.player_id)}`}
                    className="flex items-center gap-2.5 hover:text-primary"
                  >
                    <PlayerAvatar
                      photoUrl={c.photo_url}
                      name={c.name}
                      size="sm"
                    />
                    <span className="font-medium">{c.name}</span>
                  </Link>
                </td>
                <td className="px-3 py-2 text-muted-foreground hidden md:table-cell">
                  {c.primary_position}
                </td>
                <td className="px-3 py-2 text-muted-foreground hidden lg:table-cell">
                  {c.team}
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2 justify-end">
                    <div className="h-1.5 w-16 rounded-full bg-secondary overflow-hidden shrink-0">
                      <div
                        className="h-full bg-primary"
                        style={{ width: `${Math.max(0, Math.min(100, c.similarity * 100))}%` }}
                      />
                    </div>
                    <span className="font-mono text-xs w-12 text-right" data-numeric>
                      {fmtPct(c.similarity, 1)}
                    </span>
                  </div>
                </td>
                <td className="px-3 py-2 text-right font-mono text-xs text-muted-foreground hidden sm:table-cell" data-numeric>
                  {fmtNum(c.versatility_score, 2)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
