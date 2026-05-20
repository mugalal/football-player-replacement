"use client";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { ProgressIndicator } from "@/components/common/ProgressIndicator";
import { AppShell } from "@/components/layout/AppShell";
import { FilterSidebar, DEFAULT_FILTERS, filterStateToBackend, type FilterState } from "@/components/search/FilterSidebar";
import { IntensityControl } from "@/components/search/IntensityControl";
import { CandidatePodium } from "@/components/search/CandidatePodium";
import { PlayerAutocomplete } from "@/components/search/PlayerAutocomplete";
import { ResultsTable } from "@/components/search/ResultsTable";
import { SourcePlayerHero } from "@/components/search/SourcePlayerHero";
import { UpgradePicker } from "@/components/search/UpgradePicker";
import { Button } from "@/components/ui/button";
import { useSearch } from "@/lib/hooks/useSearch";
import type { PlayerSummary } from "@/lib/types";

export default function ReplacePage() {
  const [source, setSource] = useState<PlayerSummary | null>(null);
  const [selectedUpgrades, setSelectedUpgrades] = useState<Set<string>>(new Set());
  const [perUpgrade, setPerUpgrade] = useState(false);
  const [uniformIntensity, setUniformIntensity] = useState(0.5);
  const [perUpgradeIntensities, setPerUpgradeIntensities] = useState<Record<string, number>>({});
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const { state, run, reset } = useSearch();

  const selectedKeys = useMemo(() => Array.from(selectedUpgrades), [selectedUpgrades]);

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

  const canSearch = !!source && state.status !== "submitting" && state.status !== "polling";

  const onSearch = () => {
    if (!source) return;
    const upgradesBody = (() => {
      if (selectedKeys.length === 0) return undefined;
      if (perUpgrade) {
        const dict: Record<string, number> = {};
        for (const k of selectedKeys) {
          dict[k] = perUpgradeIntensities[k] ?? uniformIntensity;
        }
        return dict;
      }
      return selectedKeys;
    })();

    run({
      sources: [source.player_id],
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
            Single source · similarity or upgrade
          </span>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Replace a Player</h1>
          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
            Pick a source. Without upgrades, results are pure similarity (&lt;1s).
            With upgrades, per-match inference runs against the source&apos;s tokens — 30–60s.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-8">
          {/* LEFT RAIL — controls */}
          <aside className="space-y-7 lg:sticky lg:top-20 lg:self-start">
            <section>
              <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2.5">
                Source player
              </h3>
              {source ? (
                <SourcePlayerHero
                  player={source}
                  onRemove={() => {
                    setSource(null);
                    reset();
                  }}
                />
              ) : (
                <PlayerAutocomplete onSelect={(p) => setSource(p)} autoFocus />
              )}
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
                  <Search className="h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </aside>

          {/* MAIN — results */}
          <section>
            {state.status === "idle" && (
              <EmptyState
                title="Pick a source player and click Search"
                description="Without upgrades, results are pure similarity (<1s). Adding upgrades runs per-match inference and takes 30–60s."
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
                  <EmptyState
                    title="No candidates matched"
                    description="Try loosening filters or removing some upgrades."
                  />
                ) : (
                  <>
                    <CandidatePodium candidates={state.result.candidates} />
                    <ResultsTable candidates={state.result.candidates} skipTop3 />
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
