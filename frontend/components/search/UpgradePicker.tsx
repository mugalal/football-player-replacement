"use client";
import { useUpgrades } from "@/lib/hooks/useUpgrades";

import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { UpgradeSpec } from "@/lib/types";

interface UpgradePickerProps {
  selected: Set<string>;
  onToggle: (key: string, checked: boolean) => void;
}

export function UpgradePicker({ selected, onToggle }: UpgradePickerProps) {
  const { data, isLoading, isError } = useUpgrades();

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading upgrades…</p>;
  }
  if (isError || !data) {
    return (
      <p className="text-sm text-destructive">
        Failed to load upgrade catalog from backend.
      </p>
    );
  }

  return (
    <Tabs defaultValue="onball">
      <TabsList className="w-full">
        <TabsTrigger value="onball" className="flex-1">
          On-ball ({data.onball.length})
        </TabsTrigger>
        <TabsTrigger value="offball" className="flex-1">
          Off-ball ({data.offball.length})
        </TabsTrigger>
      </TabsList>
      <TabsContent value="onball">
        <UpgradeList items={data.onball} selected={selected} onToggle={onToggle} />
      </TabsContent>
      <TabsContent value="offball">
        <UpgradeList items={data.offball} selected={selected} onToggle={onToggle} />
      </TabsContent>
    </Tabs>
  );
}

function UpgradeList({
  items,
  selected,
  onToggle,
}: {
  items: UpgradeSpec[];
  selected: Set<string>;
  onToggle: (key: string, checked: boolean) => void;
}) {
  return (
    <ul className="space-y-1.5">
      {items.map((u) => {
        const isChecked = selected.has(u.key);
        return (
          <li key={u.key}>
            <label className="flex items-start gap-2.5 rounded-md px-2 py-1.5 hover:bg-accent transition-colors cursor-pointer">
              <Checkbox
                checked={isChecked}
                onCheckedChange={(v) => onToggle(u.key, v)}
                className="mt-0.5"
              />
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium">{u.label}</div>
                <div className="text-xs text-muted-foreground">{u.description}</div>
              </div>
            </label>
          </li>
        );
      })}
    </ul>
  );
}
