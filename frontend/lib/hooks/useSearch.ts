"use client";
import { useEffect, useRef, useState } from "react";

import { getSearchJob, isJobAccepted, submitSearch } from "@/lib/api/search";
import type { SearchRequest, SearchResponse } from "@/lib/types";

type SearchState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "polling"; jobId: string; elapsedMs: number }
  | { status: "done"; result: SearchResponse }
  | { status: "error"; message: string };

const POLL_INTERVAL_MS = 2_000;

export function useSearch() {
  const [state, setState] = useState<SearchState>({ status: "idle" });
  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const runIdRef = useRef(0);

  useEffect(() => () => clearActiveWork(), []);

  function clearActiveWork() {
    abortRef.current?.abort();
    abortRef.current = null;
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }

  function reset() {
    runIdRef.current += 1;
    clearActiveWork();
    setState({ status: "idle" });
  }

  async function run(request: SearchRequest) {
    runIdRef.current += 1;
    const runId = runIdRef.current;
    clearActiveWork();

    const controller = new AbortController();
    abortRef.current = controller;
    setState({ status: "submitting" });

    try {
      const response = await submitSearch(request, controller.signal);
      if (runId !== runIdRef.current) return;

      if (isJobAccepted(response)) {
        pollJob(response.job_id, runId, Date.now());
        return;
      }

      setState({ status: "done", result: response });
    } catch (error) {
      if (controller.signal.aborted || runId !== runIdRef.current) return;
      setState({ status: "error", message: errorMessage(error) });
    }
  }

  function pollJob(jobId: string, runId: number, startedAt: number) {
    setState({ status: "polling", jobId, elapsedMs: Date.now() - startedAt });

    timerRef.current = setTimeout(async () => {
      try {
        const job = await getSearchJob(jobId);
        if (runId !== runIdRef.current) return;

        if (job.status === "done") {
          if (!job.result) {
            setState({ status: "error", message: "Search job finished without a result." });
            return;
          }
          setState({ status: "done", result: job.result });
          return;
        }

        if (job.status === "error") {
          setState({ status: "error", message: job.error || "Search job failed." });
          return;
        }

        pollJob(jobId, runId, startedAt);
      } catch (error) {
        if (runId !== runIdRef.current) return;
        setState({ status: "error", message: errorMessage(error) });
      }
    }, POLL_INTERVAL_MS);
  }

  return { state, run, reset };
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
