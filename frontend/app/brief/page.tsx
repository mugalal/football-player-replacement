"use client";
import { Plus, Search, Sparkles } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ProgressIndicator } from "@/components/common/ProgressIndicator";
import { AppShell } from "@/components/layout/AppShell";
import {
  DEFAULT_FILTERS,
  FilterSidebar,
  filterStateToBackend,
  type FilterState,
} from "@/components/search/FilterSidebar";
import { IntensityControl } from "@/components/search/IntensityControl";
import { PlayerAutocomplete } from "@/components/search/PlayerAutocomplete";
import { PlayerCard } from "@/components/search/PlayerCard";
import { CandidatePodium } from "@/components/search/CandidatePodium";
import { ResultsTable } from "@/components/search/ResultsTable";
import { UpgradePicker } from "@/components/search/UpgradePicker";
import { Button } from "@/components/ui/button";
import { searchPlayers } from "@/lib/api/players";
import { useSearch } from "@/lib/hooks/useSearch";
import type { PlayerSummary } from "@/lib/types";

// Mané validation preset — kept in sync with backend
// services/mane_preset.py (LIVERPOOL_2015_16_ATTACKERS,
// KLOPP_UPGRADES_VALIDATED). If those constants drift, update here too.
const MANE_PRESET_NAMES = [
  "Lallana",
  "Firmino",
  "Sturridge",
  "Origi",
  "Ibe",
  "Benteke",
] as const;

const KLOPP_INTENSITIES: Record<string, number> = {
  cut_inside: 0.7,
  finishing: 0.5,
  progression: 0.4,
  chance_creation: 0.4,
  dribbling: 0.4,
  pressing: 0.7,
};

function BriefPageInner() {
  const searchParams = useSearchParams();
  const preset = searchParams?.get("preset");

  const [sources, setSources] = useState<PlayerSummary[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [presetState, setPresetState] = useState<"idle" | "loading" | "loaded" | "failed">(
    "idle",
  );

  const [selectedUpgrades, setSelectedUpgrades] = useState<Set<string>>(new Set());
  const [perUpgrade, setPerUpgrade] = useState(false);
  const [uniformIntensity, setUniformIntensity] = useState(0.5);
  const [perUpgradeIntensities, setPerUpgradeIntensities] = useState<Record<string, number>>({});
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const { state, run, reset } = useSearch();

  const selectedKeys = useMemo(() => Array.from(selectedUpgrades), [selectedUpgrades]);

  // Load Mané preset on mount (one-shot, do not auto-run search).
  useEffect(() => {
    if (preset !== "mane" || presetState !== "idle") return;
    setPresetState("loading");

    (async () => {
      try {
        const resolved: PlayerSummary[] = [];
        for (const name of MANE_PRESET_NAMES) {
          // Engine resolves by name; we use the first match.
          const matches = await searchPlayers(name, 5);
          const exact = matches.find(
            (m) => m.name.toLowerCase().includes(name.toLowerCase()),
          );
          if (exact) resolved.push(exact);
        }
        setSources(resolved);
        setSelectedUpgrades(new Set(Object.keys(KLOPP_INTENSITIES)));
        setPerUpgrade(true);
        setPerUpgradeIntensities({ ...KLOPP_INTENSITIES });
        setPresetState("loaded");
      } catch {
        setPresetState("failed");
      }
    })();
  }, [preset, presetState]);

  const onToggleUpgrade = (key: string, checked: boolean) => {
    setSelectedUpgrades((prev) => {
      const next = new Set(prev);
      if (checked) next.add(key);
      else next.delete(key);
      return next;
    });
    if (checked && !(key in perUpgradeIntensities)) {
      setPerUpgradeIntensities((prev) => ({ ...prev, [key]: uniformIntensity }));
    }
  };

  const canSearch =
    sources.length > 0 && state.status !== "submitting" && state.status !== "polling";

  const onSearch = () => {
    if (sources.length === 0) return;
    const upgradesBody = (() => {
      if (selectedKeys.length === 0) return undefined;
      if (perUpgrade) {
        const dict: Record<string, number> = {};
        for (const k of selectedKeys) dict[k] = perUpgradeIntensities[k] ?? uniformIntensity;
        return dict;
      }
      return selectedKeys;
    })();
    run({
      sources: sources.map((s) => s.player_id),
      upgrades: upgradesBody,
      upgrade_intensity: uniformIntensity,
      top_k: 30,
      filters: filterStateToBackend(filters),
    });
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        <header className="mb-8 max-w-2xl">
          <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
            Multi-source · weighted pooling
          </span>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Scouting Brief</h1>
          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
            Pool several source players into a single target profile, then search
            for who fits. Use this when you&apos;re replacing a role, not just
            one name.
          </p>
        </header>

        {preset === "mane" && (
          <div className="mb-6 rounded-md border border-primary/40 bg-primary/5 p-4">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div className="flex-1 text-sm">
                {presetState === "loading" && (
                  <p className="flex items-center gap-2">
                    <LoadingSpinner /> Loading Mané preset…
                  </p>
                )}
                {presetState === "loaded" && (
                  <>
                    <p className="font-medium">Mané validation inputs loaded. Click Search to run.</p>
                    <p className="mt-1 text-muted-foreground">
                      This view does not filter defenders or show the verdict. For the
                      official validation result, see{" "}
                      <Link href="/validations/mane" className="underline hover:text-primary">
                        /validations/mane
                      </Link>
                      .
                    </p>
                  </>
                )}
                {presetState === "failed" && (
                  <p className="text-destructive">
                    Failed to resolve some preset players. The backend may be warming up — refresh
                    and try again.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-8">
          {/* LEFT RAIL */}
          <aside className="space-y-7 lg:sticky lg:top-20 lg:self-start max-h-[calc(100vh-6rem)] overflow-y-auto pr-1">
            <section>
              <div className="flex items-baseline justify-between mb-2.5">
                <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Sources
                </h3>
                <span className="text-[10px] font-mono text-muted-foreground" data-numeric>
                  {sources.length} player{sources.length === 1 ? "" : "s"}
                </span>
              </div>
              <div className="space-y-2">
                {sources.map((s) => (
                  <PlayerCard
                    key={s.player_id}
                    player={s}
                    compact
                    onRemove={() => {
                      setSources((prev) => prev.filter((p) => p.player_id !== s.player_id));
                      reset();
                    }}
                  />
                ))}
                {showAdd ? (
                  <div className="space-y-2">
                    <PlayerAutocomplete
                      autoFocus
                      onSelect={(p) => {
                        setSources((prev) =>
                          prev.some((x) => x.player_id === p.player_id) ? prev : [...prev, p],
                        );
                        setShowAdd(false);
                      }}
                    />
                    <Button variant="ghost" size="sm" onClick={() => setShowAdd(false)}>
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAdd(true)}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4" /> Add source
                  </Button>
                )}
              </div>
            </section>

            <section>
              <div className="flex items-baseline justify-between mb-2.5">
                <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Upgrades
                </h3>
                {selectedKeys.length > 0 && (
                  <span className="text-[10px] font-mono text-primary" data-numeric>
                    {selectedKeys.length} selected
                  </span>
                )}
              </div>
              <UpgradePicker selected={selectedUpgrades} onToggle={onToggleUpgrade} />
            </section>

            {selectedKeys.length > 0 && (
              <section>
                <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2.5">
                  Intensity
                </h3>
                <IntensityControl
                  selectedKeys={selectedKeys}
                  perUpgrade={perUpgrade}
                  uniformIntensity={uniformIntensity}
                  perUpgradeIntensities={perUpgradeIntensities}
                  onUniformChange={setUniformIntensity}
                  onPerUpgradeToggle={setPerUpgrade}
                  onPerUpgradeChange={(k, v) =>
                    setPerUpgradeIntensities((prev) => ({ ...prev, [k]: v }))
                  }
                />
              </section>
            )}

            <FilterSidebar value={filters} onChange={setFilters} />

            <Button onClick={onSearch} disabled={!canSearch} className="w-full" size="lg">
              {state.status === "submitting" || state.status === "polling" ? (
                "Searching…"
              ) : (
                <>
                  <Search className="h-4 w-4" /> Search
                </>
              )}
            </Button>
          </aside>

          {/* MAIN */}
          <section>
            {state.status === "idle" && (
              <EmptyState
                title={
                  sources.length === 0
                    ? "Add at least one source player"
                    : "Click Search to run"
                }
                description="Multi-source pools combine the source players' patterns into a single target profile."
                icon={<Search className="h-8 w-8" />}
              />
            )}

            {(state.status === "submitting" || state.status === "polling") && (
              <ProgressIndicator
                message={
                  state.status === "submitting"
                    ? "Submitting search…"
                    : "Processing upgraded profile search."
                }
                elapsedMs={state.status === "polling" ? state.elapsedMs : 0}
              />
            )}

            {state.status === "error" && (
              <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
                <p className="font-medium">Search failed</p>
                <p className="mt-1 text-destructive/80">{state.message}</p>
                <Button variant="outline" size="sm" className="mt-3" onClick={onSearch}>
                  Retry
                </Button>
              </div>
            )}

            {state.status === "done" && (
              <>
                {state.result.warnings.length > 0 && (
                  <ul className="mb-4 rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-xs text-amber-700 dark:text-amber-300 space-y-0.5">
                    {state.result.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                )}
                {state.result.candidates.length === 0 ? (
                  <EmptyState title="No candidates matched" description="Try loosening filters." />
                ) : (
                  <>
                    <CandidatePodium
                      candidates={state.result.candidates}
                      highlightName={preset === "mane" ? "Mané" : undefined}
                    />
                    <ResultsTable
                      candidates={state.result.candidates}
                      highlightName={preset === "mane" ? "Mané" : undefined}
                      skipTop3
                    />
                  </>
                )}
              </>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}

// useSearchParams must be wrapped in Suspense per Next.js 14 requirements.
export default function BriefPage() {
  return (
    <Suspense fallback={null}>
      <BriefPageInner />
    </Suspense>
  );
}
