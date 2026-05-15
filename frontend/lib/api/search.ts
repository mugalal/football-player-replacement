import { apiFetch } from "@/lib/api/client";
import type { JobAcceptedResponse, JobRecord, SearchRequest, SearchResponse } from "@/lib/types";

export type SearchSubmitResponse = SearchResponse | JobAcceptedResponse;

export function submitSearch(request: SearchRequest, signal?: AbortSignal) {
  return apiFetch<SearchSubmitResponse>("/api/search", {
    method: "POST",
    body: JSON.stringify(request),
    signal,
  });
}

export function getSearchJob(jobId: string, signal?: AbortSignal) {
  return apiFetch<JobRecord>(`/api/search/${encodeURIComponent(jobId)}`, { signal });
}

export function isJobAccepted(response: SearchSubmitResponse): response is JobAcceptedResponse {
  return "job_id" in response;
}
