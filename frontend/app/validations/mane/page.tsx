"use client";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, CheckCircle2, Loader2, XCircle } from "lucide-react";
import Link from "next/link";

import { AppShell } from "@/components/layout/AppShell";
import { PitchHeatmap } from "@/components/player/PitchHeatmap";
import { ResultsTable } from "@/components/search/ResultsTable";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { getManeHeatmap, getManeValidation } from "@/lib/api/validations";
import type { Verdict } from "@/lib/types";
import { cn } from "@/lib/utils";

const KLOPP_UPGRADES: Record<string, number> = {
  cut_inside: 0.7,
  finishing: 0.5,
  progression: 0.4,
  chance_creation: 0.4,
  dribbling: 0.4,
  pressing: 0.7,
};

const VERDICT_STYLES: Record<Verdict, { tone: string; ring: string; Icon: typeof CheckCircle2 }> = {
  EXCELLENT:  { tone: "text-emerald-700 dark:text-emerald-300", ring: "border-emerald-500/40 bg-emerald-500/5", Icon: CheckCircle2 },
  STRONG:     { tone: "text-emerald-700 dark:text-emerald-300", ring: "border-emerald-500/40 bg-emerald-500/5", Icon: CheckCircle2 },
  ACCEPTABLE: { tone: "text-amber-700 dark:text-amber-300",     ring: "border-amber-500/40 bg-amber-500/5",     Icon: AlertTriangle },
  MARGINAL:   { tone: "text-amber-700 dark:text-amber-300",     ring: "border-amber-500/40 bg-amber-500/5",     Icon: AlertTriangle },
  FAIL:       { tone: "text-destructive",                       ring: "border-destructive/40 bg-destructive/5", Icon: XCircle },
};

export default function ManeValidationPage() {
  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ["mane-validation"],
    queryFn: getManeValidation,
    staleTime: Infinity,
    retry: false,
  });

  const { data: heatmap } = useQuery({
    queryKey: ["mane-heatmap"],
    queryFn: getManeHeatmap,
    staleTime: Infinity,
    retry: false,
    // Don't block the page on this — the verdict is the headline; the
    // heatmap is the "why" and can arrive a little later.
    enabled: !!data,
  });

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        <header className="max-w-3xl">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
              Locked regression
            </span>
          </div>
          <h1 className="text-3xl font-semibold tracking-tight">Mané Validation</h1>
          <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
            Given Liverpool&apos;s 2015-16 attacking pool and Klopp-style upgrades,
            the methodology should rank Sadio Mané — Liverpool&apos;s actual 2016
            signing — high among attacking candidates from the full ~2,200 player
            dataset. Defensive positions are filtered out: Klopp&apos;s brief was for
            an attacker.
          </p>
        </header>

        {(isLoading || isFetching) && !data && (
          <Card>
            <CardContent className="p-6 flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              <div className="text-sm">
                <p className="font-medium">Running validation (one-time, ~30–60 s)…</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  The result is cached server-side after the first run.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {error && (
          <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
            <p className="font-medium">Validation failed</p>
            <p className="mt-1 text-destructive/80">
              {error instanceof Error ? error.message : String(error)}
            </p>
            <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        )}

        {data && (
          <>
            <VerdictHero
              verdict={data.verdict}
              description={data.verdict_description}
              rank={data.mane_rank}
              candidatePool={data.candidates.length}
              defendersFiltered={data.filtered_defender_count}
            />

            {heatmap && (
              <>
                <Card>
                  <CardContent className="p-6">
                    <div className="mb-5 max-w-2xl">
                      <CardTitle className="text-base">Why this works — spatial profile</CardTitle>
                      <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">
                        The methodology recovers Mané because his on-pitch footprint matches
                        the Liverpool 2015-16 attacking pool. Each cell is a 6×3 zone on a
                        120×80 pitch (StatsBomb coordinates), heat-tinted by total
                        on-ball + off-ball actions. Attacking direction is left-to-right.
                      </p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      <PitchHeatmap
                        counts={heatmap.pool.counts}
                        total={heatmap.pool.total}
                        numX={heatmap.num_x}
                        numY={heatmap.num_y}
                        title="Source pool"
                        subtitle={heatmap.pool.source_names?.join(" · ") ?? heatmap.pool.label}
                      />
                      {heatmap.mane.counts && heatmap.mane.counts.length > 0 ? (
                        <PitchHeatmap
                          counts={heatmap.mane.counts}
                          total={heatmap.mane.total}
                          numX={heatmap.num_x}
                          numY={heatmap.num_y}
                          title="Sadio Mané"
                          subtitle="Southampton, 2015-16"
                        />
                      ) : (
                        <div className="rounded-md border border-dashed border-border p-6 text-sm text-muted-foreground">
                          Mané heatmap unavailable — player not resolved in the dataset.
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {heatmap.top_candidates && heatmap.top_candidates.length > 0 && (
                  <Card>
                    <CardContent className="p-6">
                      <div className="mb-5 max-w-2xl">
                        <CardTitle className="text-base">Top 5 candidates — spatial check</CardTitle>
                        <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">
                          Heatmaps for the 5 attackers the methodology surfaced first.
                          All five share the same wide-attacking footprint as the source
                          pool — that&apos;s exactly the signal the ranking is picking up.
                        </p>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                        {heatmap.top_candidates.map((c) => (
                          <Link
                            key={c.player_id}
                            href={`/player/${encodeURIComponent(c.player_id)}`}
                            className={cn(
                              "block rounded-lg border p-3 transition-colors hover:bg-accent/40",
                              c.is_mane
                                ? "border-primary/50 bg-primary/5 hover:bg-primary/10"
                                : "border-border",
                            )}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="inline-flex items-center justify-center h-6 min-w-6 px-1.5 rounded text-[11px] font-mono bg-muted text-muted-foreground" data-numeric>
                                #{c.attacker_rank}
                              </span>
                              <span className="font-mono text-[10px] text-muted-foreground tabular-nums" data-numeric>
                                {(c.similarity * 100).toFixed(1)}%
                              </span>
                            </div>
                            <PitchHeatmap
                              counts={c.counts}
                              total={c.total}
                              numX={heatmap.num_x}
                              numY={heatmap.num_y}
                            />
                            <div className="mt-2.5">
                              <div className="text-xs font-medium truncate" title={c.name}>
                                {c.name}
                              </div>
                              <div className="text-[10px] text-muted-foreground truncate mt-0.5">
                                {c.primary_position} · {c.team}
                              </div>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <CardTitle className="text-base">
                      Top {data.candidates.length} attackers
                    </CardTitle>
                    <Badge variant="secondary" className="text-[10px] uppercase tracking-wider">
                      Defenders filtered
                    </Badge>
                  </div>
                  <ResultsTable
                    candidates={data.candidates}
                    showAttackerRank
                    highlightName="Mané"
                  />
                </CardContent>
              </Card>

              <aside className="space-y-4">
                <Card>
                  <CardContent className="p-5">
                    <CardTitle className="text-sm">Source pool</CardTitle>
                    <p className="mt-1 text-[11px] text-muted-foreground">
                      Liverpool 2015-16 attackers
                    </p>
                    <ul className="mt-3 space-y-1.5 text-sm">
                      {data.query.sources.map((s) => (
                        <li key={s.player_id} className="flex justify-between gap-2 leading-tight">
                          <span className="truncate font-medium">{s.name}</span>
                          <span className="text-[10px] text-muted-foreground shrink-0 self-center font-mono uppercase tracking-wider">
                            {s.primary_position.split(" ").map(w => w[0]).join("")}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-5">
                    <CardTitle className="text-sm">Klopp upgrades</CardTitle>
                    <p className="mt-1 text-[11px] text-muted-foreground">
                      Per-upgrade probabilities (regression checkpoint)
                    </p>
                    <ul className="mt-3 space-y-2">
                      {Object.entries(KLOPP_UPGRADES).map(([k, v]) => (
                        <li key={k} className="space-y-1">
                          <div className="flex justify-between gap-2 text-xs">
                            <span className="capitalize">{k.replace(/_/g, " ")}</span>
                            <span className="font-mono text-muted-foreground tabular-nums" data-numeric>
                              {(v * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-1 rounded-full bg-secondary overflow-hidden">
                            <div
                              className="h-full bg-primary/70 rounded-full"
                              style={{ width: `${v * 100}%` }}
                            />
                          </div>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Link
                  href="/brief?preset=mane"
                  className={cn(buttonVariants({ variant: "outline" }), "w-full")}
                >
                  Open in scouting brief <ArrowRight className="h-4 w-4" />
                </Link>
              </aside>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

function VerdictHero({
  verdict,
  description,
  rank,
  candidatePool,
  defendersFiltered,
}: {
  verdict: Verdict;
  description: string;
  rank: number | null;
  candidatePool: number;
  defendersFiltered: number;
}) {
  const { tone, ring, Icon } = VERDICT_STYLES[verdict];
  return (
    <div className={cn("rounded-xl border p-6 sm:p-8", ring)}>
      <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-6 items-center">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Icon className={cn("h-5 w-5", tone)} />
            <span className={cn("text-[11px] font-mono uppercase tracking-wider", tone)}>
              Verdict
            </span>
          </div>
          <h2 className={cn("text-3xl sm:text-4xl font-semibold tracking-tight", tone)}>
            {verdict}
          </h2>
          <p className="mt-2 text-sm text-foreground/80 max-w-xl leading-relaxed">
            {description}
          </p>
        </div>

        {rank !== null && (
          <div className="flex sm:flex-col items-center sm:items-end gap-4 sm:gap-1 sm:text-right">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                Mané rank
              </div>
              <div className={cn("text-5xl sm:text-6xl font-semibold font-mono tabular-nums", tone)} data-numeric>
                #{rank}
              </div>
            </div>
            <div className="text-xs text-muted-foreground font-mono tabular-nums" data-numeric>
              of {candidatePool} attackers
              <span className="mx-1.5 opacity-50">·</span>
              {defendersFiltered} defenders filtered
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
