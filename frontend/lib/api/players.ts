import { apiFetch } from "@/lib/api/client";
import type { Candidate, PlayerDetail, PlayerHeatmap, PlayerSummary } from "@/lib/types";

export function searchPlayers(query: string, limit = 20, signal?: AbortSignal) {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return apiFetch<PlayerSummary[]>(`/api/players?${params.toString()}`, { signal });
}

export function getPlayer(playerId: string, signal?: AbortSignal) {
  return apiFetch<PlayerDetail>(`/api/players/${encodeURIComponent(playerId)}`, { signal });
}

export function getSimilar(playerId: string, topK = 10, signal?: AbortSignal) {
  const params = new URLSearchParams({ top_k: String(topK) });
  return apiFetch<Candidate[]>(`/api/players/${encodeURIComponent(playerId)}/similar?${params.toString()}`, { signal });
}

export function getPlayerHeatmap(playerId: string, signal?: AbortSignal) {
  return apiFetch<PlayerHeatmap>(`/api/players/${encodeURIComponent(playerId)}/heatmap`, { signal });
}
