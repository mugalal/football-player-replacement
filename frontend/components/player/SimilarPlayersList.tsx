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
    <ul className="divide-y divide-border rounded-md border border-border overflow-hidden">
      {data.map((c) => (
        <li key={c.player_id}>
          <Link
            href={`/player/${encodeURIComponent(c.player_id)}`}
            className="flex items-center gap-3 px-3 py-2.5 hover:bg-accent transition-colors"
          >
            <span className="text-xs font-mono text-muted-foreground w-5 text-right" data-numeric>
              {c.rank}
            </span>
            <PlayerAvatar photoUrl={c.photo_url} name={c.name} size="sm" />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium truncate">{c.name}</div>
              <div className="text-xs text-muted-foreground truncate">
                {c.primary_position} · {c.team}
              </div>
            </div>
            <div className="text-xs font-mono text-muted-foreground shrink-0" data-numeric>
              {fmtPct(c.similarity, 1)}
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
