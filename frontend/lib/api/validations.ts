import { apiFetch } from "@/lib/api/client";
import type { ManeHeatmapResponse, ManeValidationResponse } from "@/lib/types";

type SignalArg = AbortSignal | { signal?: AbortSignal };

export function getManeValidation(arg?: SignalArg) {
  const signal = arg instanceof AbortSignal ? arg : arg?.signal;
  return apiFetch<ManeValidationResponse>("/api/validations/mane", { signal });
}

export function getManeHeatmap(arg?: SignalArg) {
  const signal = arg instanceof AbortSignal ? arg : arg?.signal;
  return apiFetch<ManeHeatmapResponse>("/api/validations/mane/heatmap", { signal });
}
