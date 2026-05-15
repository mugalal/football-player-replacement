import { apiFetch } from "@/lib/api/client";
import type { HealthResponse } from "@/lib/types";

export function getHealth(signal?: AbortSignal) {
  return apiFetch<HealthResponse>("/api/health", { signal });
}
