"use client";
import { useQuery } from "@tanstack/react-query";

import { getFilters } from "@/lib/api/catalog";

export function useFilters() {
  return useQuery({
    queryKey: ["filters"],
    queryFn: ({ signal }) => getFilters(signal),
    staleTime: 10 * 60 * 1000,
  });
}
