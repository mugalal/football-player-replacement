import { apiFetch } from "@/lib/api/client";
import type { FilterCatalog, UpgradeCatalog } from "@/lib/types";

export function getUpgrades(signal?: AbortSignal) {
  return apiFetch<UpgradeCatalog>("/api/upgrades", { signal });
}

export function getFilters(signal?: AbortSignal) {
  return apiFetch<FilterCatalog>("/api/filters", { signal });
}
