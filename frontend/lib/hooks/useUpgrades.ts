"use client";
import { useQuery } from "@tanstack/react-query";

import { getUpgrades } from "@/lib/api/catalog";

export function useUpgrades() {
  return useQuery({
    queryKey: ["upgrades"],
    queryFn: ({ signal }) => getUpgrades(signal),
    staleTime: 10 * 60 * 1000,
  });
}
