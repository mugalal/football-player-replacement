"use client";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
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
  return (
    <section>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">
        Filters
      </h3>
      <div className="space-y-5">
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <Label className="text-xs">Min versatility</Label>
            <span className="text-xs font-mono text-muted-foreground" data-numeric>
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
