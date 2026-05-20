"use client";
import { useQuery } from "@tanstack/react-query";
import { Home } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { AppShell } from "@/components/layout/AppShell";
import { PitchHeatmap } from "@/components/player/PitchHeatmap";
import { PlayerHeader } from "@/components/player/PlayerHeader";
import { SimilarPlayersList } from "@/components/player/SimilarPlayersList";
import { PositionDistributionChart } from "@/components/search/PositionDistributionChart";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { getPlayer, getPlayerHeatmap } from "@/lib/api/players";
import { ApiError } from "@/lib/api/client";
import { cn } from "@/lib/utils";

export default function PlayerPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? "";

  const { data, isLoading, error } = useQuery({
    queryKey: ["player", id],
    queryFn: () => getPlayer(id),
    enabled: !!id,
  });

  const { data: heatmap } = useQuery({
    queryKey: ["player-heatmap", id],
    queryFn: () => getPlayerHeatmap(id),
    enabled: !!id && !!data,
    staleTime: Infinity,
    retry: false,
  });

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8">
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <LoadingSpinner /> Loading player…
          </div>
        )}

        {error instanceof ApiError && error.status === 404 && (
          <EmptyState
            title="Player not found"
            description={`No player with ID "${id}" in the dataset.`}
            action={
              <Link href="/" className={cn(buttonVariants({ variant: "outline" }))}>
                <Home className="h-4 w-4" /> Back to home
              </Link>
            }
          />
        )}

        {error && !(error instanceof ApiError && error.status === 404) && (
          <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
            Failed to load player: {error instanceof Error ? error.message : String(error)}
          </div>
        )}

        {data && (
          <div className="space-y-6">
            <PlayerHeader player={data} />

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
              <div className="space-y-6">
                <Card>
                  <CardContent className="p-6">
                    <CardTitle className="text-base mb-4">Position distribution</CardTitle>
                    <PositionDistributionChart distribution={data.position_distribution} />
                  </CardContent>
                </Card>

                {heatmap && heatmap.total > 0 && (
                  <Card>
                    <CardContent className="p-6">
                      <PitchHeatmap
                        counts={heatmap.counts}
                        total={heatmap.total}
                        numX={heatmap.num_x}
                        numY={heatmap.num_y}
                        title="Pitch heatmap"
                        subtitle={`Aggregated on-ball + off-ball actions across ${data.num_matches} matches`}
                      />
                    </CardContent>
                  </Card>
                )}
              </div>

              <Card>
                <CardContent className="p-6">
                  <CardTitle className="text-base mb-4">Top 10 similar players</CardTitle>
                  <SimilarPlayersList playerId={data.player_id} topK={10} />
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
