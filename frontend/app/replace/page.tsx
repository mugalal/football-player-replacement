"use client";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { ProgressIndicator } from "@/components/common/ProgressIndicator";
import { AppShell } from "@/components/layout/AppShell";
import { FilterSidebar, DEFAULT_FILTERS, filterStateToBackend, type FilterState } from "@/components/search/FilterSidebar";
import { IntensityControl } from "@/components/search/IntensityControl";
import { PlayerAutocomplete } from "@/components/search/PlayerAutocomplete";
import { PlayerCard } from "@/components/search/PlayerCard";
import { ResultsTable } from "@/components/search/ResultsTable";
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
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Replace a Player</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Pick a source player. Optionally apply upgrades to nudge the target profile.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
          {/* LEFT RAIL — controls */}
          <aside className="space-y-6">
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                Source player
              </h3>
              {source ? (
                <PlayerCard
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
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                Upgrades ({selectedKeys.length})
              </h3>
              <UpgradePicker selected={selectedUpgrades} onToggle={onToggleUpgrade} />
            </section>

            {selectedKeys.length > 0 && (
              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
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

            <Button onClick={onSearch} disabled={!canSearch} className="w-full">
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
                  <ResultsTable candidates={state.result.candidates} />
                )}
              </>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}
