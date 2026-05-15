"use client";
import { Lock } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { useFilters } from "@/lib/hooks/useFilters";
import { fmtNum } from "@/lib/utils";

export interface FilterState {
  minVersatility: number;
  minMatches: number;
}

export const DEFAULT_FILTERS: FilterState = {
  minVersatility: 0,
  minMatches: 5,
};

interface FilterSidebarProps {
  value: FilterState;
  onChange: (next: FilterState) => void;
}

export function FilterSidebar({ value, onChange }: FilterSidebarProps) {
  const { data: catalog } = useFilters();

  return (
    <div className="space-y-5">
      <section>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
          Filters
        </h4>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <Label className="text-xs">Min versatility</Label>
              <span className="text-xs font-mono text-muted-foreground">
                {fmtNum(value.minVersatility)}
              </span>
            </div>
            <Slider
              value={[value.minVersatility]}
              min={0}
              max={2.5}
              step={0.1}
              onValueChange={(v) => onChange({ ...value, minVersatility: v[0] ?? 0 })}
            />
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">Min matches</Label>
            <Input
              type="number"
              min={0}
              value={value.minMatches}
              onChange={(e) => {
                const n = Number(e.target.value);
                onChange({ ...value, minMatches: Number.isFinite(n) ? n : 0 });
              }}
            />
          </div>
        </div>
      </section>

      {catalog?.coming_soon && catalog.coming_soon.length > 0 && (
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            Coming soon
          </h4>
          <ul className="space-y-1">
            {catalog.coming_soon.map((k) => (
              <li
                key={k}
                title="Requires Transfermarkt integration"
                className="flex items-center gap-2 text-xs text-muted-foreground/70 select-none"
              >
                <Lock className="h-3 w-3 shrink-0" />
                {k.replace(/_/g, " ")}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-[10px] text-muted-foreground/60 leading-relaxed">
            Age, league, and market-value filters require a Transfermarkt-style data
            source that isn&apos;t wired up in v1.
          </p>
        </section>
      )}
    </div>
  );
}

export function filterStateToBackend(
  state: FilterState,
): Record<string, unknown> {
  // Engine accepts these keys in `filters`. We only send keys with non-default values.
  const out: Record<string, unknown> = {};
  if (state.minVersatility > 0) out.min_versatility = state.minVersatility;
  if (state.minMatches !== 5) out.min_matches = state.minMatches;
  return out;
}
