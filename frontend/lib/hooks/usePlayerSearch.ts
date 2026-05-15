"use client";
import { useQuery } from "@tanstack/react-query";

import { searchPlayers } from "@/lib/api/players";

export function usePlayerSearch(query: string, limit = 20) {
  const trimmed = query.trim();
  return useQuery({
    queryKey: ["players", trimmed, limit],
    queryFn: ({ signal }) => searchPlayers(trimmed, limit, signal),
    enabled: trimmed.length > 0,
    staleTime: 60_000,
  });
}
