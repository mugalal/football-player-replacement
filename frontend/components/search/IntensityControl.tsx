"use client";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { fmtPct } from "@/lib/utils";

interface IntensityControlProps {
  selectedKeys: string[];
  perUpgrade: boolean;
  uniformIntensity: number;
  perUpgradeIntensities: Record<string, number>;
  onUniformChange: (v: number) => void;
  onPerUpgradeToggle: (enabled: boolean) => void;
  onPerUpgradeChange: (key: string, v: number) => void;
}

export function IntensityControl({
  selectedKeys,
  perUpgrade,
  uniformIntensity,
  perUpgradeIntensities,
  onUniformChange,
  onPerUpgradeToggle,
  onPerUpgradeChange,
}: IntensityControlProps) {
  if (selectedKeys.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">
        Select one or more upgrades above to set their intensity.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 cursor-pointer text-xs text-muted-foreground select-none">
        <input
          type="checkbox"
          checked={perUpgrade}
          onChange={(e) => onPerUpgradeToggle(e.target.checked)}
          className="accent-primary"
        />
        Per-upgrade intensities
      </label>

      {!perUpgrade && (
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <Label className="text-xs">Uniform intensity</Label>
            <span className="text-xs font-mono text-muted-foreground">
              {fmtPct(uniformIntensity)}
            </span>
          </div>
          <Slider
            value={[uniformIntensity]}
            min={0}
            max={1}
            step={0.05}
            onValueChange={(v) => onUniformChange(v[0] ?? 0)}
          />
        </div>
      )}

      {perUpgrade && (
        <ul className="space-y-2.5">
          {selectedKeys.map((key) => {
            const v = perUpgradeIntensities[key] ?? uniformIntensity;
            return (
              <li key={key}>
                <div className="flex items-center justify-between mb-1">
                  <Label className="text-xs">{key.replace(/_/g, " ")}</Label>
                  <span className="text-xs font-mono text-muted-foreground">
                    {fmtPct(v)}
                  </span>
                </div>
                <Slider
                  value={[v]}
                  min={0}
                  max={1}
                  step={0.05}
                  onValueChange={(nv) => onPerUpgradeChange(key, nv[0] ?? 0)}
                />
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
