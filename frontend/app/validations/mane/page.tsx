"use client";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, CheckCircle2, Loader2, XCircle } from "lucide-react";
import Link from "next/link";

import { AppShell } from "@/components/layout/AppShell";
import { ResultsTable } from "@/components/search/ResultsTable";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { cn as cnUtil } from "@/lib/utils";
import { getManeValidation } from "@/lib/api/validations";
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

const VERDICT_STYLES: Record<Verdict, { tone: string; Icon: typeof CheckCircle2 }> = {
  EXCELLENT: { tone: "text-emerald-600 dark:text-emerald-400 border-emerald-500/40 bg-emerald-500/5", Icon: CheckCircle2 },
  STRONG:    { tone: "text-emerald-600 dark:text-emerald-400 border-emerald-500/40 bg-emerald-500/5", Icon: CheckCircle2 },
  ACCEPTABLE:{ tone: "text-amber-600 dark:text-amber-400 border-amber-500/40 bg-amber-500/5", Icon: AlertTriangle },
  MARGINAL:  { tone: "text-amber-600 dark:text-amber-400 border-amber-500/40 bg-amber-500/5", Icon: AlertTriangle },
  FAIL:      { tone: "text-destructive border-destructive/40 bg-destructive/5", Icon: XCircle },
};

export default function ManeValidationPage() {
  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ["mane-validation"],
    queryFn: getManeValidation,
    // Backend caches on its side; we keep the result cached client-side too.
    staleTime: Infinity,
    retry: false,
  });

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Mané Validation</h1>
          <p className="mt-1 text-sm text-muted-foreground max-w-3xl">
            Regression check: given Liverpool&apos;s 2015-16 attacking pool and Klopp-style
            upgrades, the methodology should rank Sadio Mané — Liverpool&apos;s actual 2016
            signing — high among the attacking candidates from the full ~2,200 player dataset.
            Defensive positions are filtered out (Klopp&apos;s brief was for an attacker).
          </p>
        </div>

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
            <VerdictBanner verdict={data.verdict} description={data.verdict_description} rank={data.mane_rank} />

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <CardTitle className="text-base">
                      Top {data.candidates.length} attackers (defenders filtered)
                    </CardTitle>
                    <Badge variant="secondary" className="text-[10px]">
                      {data.filtered_defender_count} defenders removed
                    </Badge>
                  </div>
                  <ResultsTable
                    candidates={data.candidates}
                    showAttackerRank
                    highlightName="Mané"
                  />
                </CardContent>
              </Card>

              <div className="space-y-4">
                <Card>
                  <CardContent className="p-5">
                    <CardTitle className="text-sm">Source pool</CardTitle>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Liverpool 2015-16 attackers
                    </p>
                    <ul className="mt-3 space-y-1 text-sm">
                      {data.query.sources.map((s) => (
                        <li key={s.player_id} className="flex justify-between gap-2">
                          <span className="truncate">{s.name}</span>
                          <span className="text-xs text-muted-foreground shrink-0">
                            {s.primary_position}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-5">
                    <CardTitle className="text-sm">Klopp upgrade profile</CardTitle>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Per-upgrade probabilities (regression checkpoint)
                    </p>
                    <ul className="mt-3 space-y-1 text-sm">
                      {Object.entries(KLOPP_UPGRADES).map(([k, v]) => (
                        <li key={k} className="flex justify-between gap-2">
                          <span className="truncate">{k.replace(/_/g, " ")}</span>
                          <span className="font-mono text-xs text-muted-foreground" data-numeric>
                            {(v * 100).toFixed(0)}%
                          </span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Link
                  href="/brief?preset=mane"
                  className={cnUtil(buttonVariants({ variant: "outline" }), "w-full")}
                >
                  Open in scouting brief <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

function VerdictBanner({
  verdict,
  description,
  rank,
}: {
  verdict: Verdict;
  description: string;
  rank: number | null;
}) {
  const { tone, Icon } = VERDICT_STYLES[verdict];
  return (
    <div className={cn("rounded-lg border p-5", tone)}>
      <div className="flex items-start gap-3">
        <Icon className="h-6 w-6 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-lg font-semibold tracking-tight">{verdict}</h2>
            {rank !== null && (
              <Badge variant="outline" className="text-xs">
                Mané attacker rank #{rank}
              </Badge>
            )}
          </div>
          <p className="mt-1 text-sm">{description}</p>
        </div>
      </div>
    </div>
  );
}
