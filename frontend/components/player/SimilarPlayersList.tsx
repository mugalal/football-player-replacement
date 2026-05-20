"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { PlayerAvatar } from "@/components/player/PlayerAvatar";
import { getSimilar } from "@/lib/api/players";
import { fmtPct } from "@/lib/utils";

interface SimilarPlayersListProps {
  playerId: string;
  topK?: number;
}

export function SimilarPlayersList({ playerId, topK = 10 }: SimilarPlayersListProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["similar", playerId, topK],
    queryFn: () => getSimilar(playerId, topK),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <LoadingSpinner /> Loading similar players…
      </div>
    );
  }
  if (isError || !data) {
    return (
      <p className="text-sm text-destructive">Failed to load similar players.</p>
    );
  }
  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">No similar players found.</p>;
  }

  return (
    <ul className="space-y-1.5">
      {data.map((c) => (
        <li key={c.player_id}>
          <Link
            href={`/player/${encodeURIComponent(c.player_id)}`}
            className="flex items-center gap-3 rounded-md border border-border/60 bg-card/40 hover:bg-accent hover:border-primary/30 p-2 transition-colors"
          >
            <span
              className="inline-flex items-center justify-center h-6 min-w-6 px-1.5 rounded text-[10px] font-mono text-muted-foreground bg-muted shrink-0"
              data-numeric
            >
              {c.rank}
            </span>
            <PlayerAvatar photoUrl={c.photo_url} name={c.name} size="md" />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium truncate leading-tight">{c.name}</div>
              <div className="text-[11px] text-muted-foreground truncate mt-0.5">
                {c.primary_position} · {c.team}
              </div>
            </div>
            <div className="shrink-0 text-right">
              <div className="text-xs font-mono font-medium text-foreground tabular-nums" data-numeric>
                {fmtPct(c.similarity, 1)}
              </div>
              <div className="mt-1 h-1 w-12 rounded-full bg-secondary overflow-hidden">
                <div
                  className="h-full bg-primary/70"
                  style={{ width: `${Math.max(0, Math.min(100, c.similarity * 100))}%` }}
                />
              </div>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
