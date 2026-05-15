"use client";
import { AlertTriangle, Loader2, WifiOff } from "lucide-react";

import { cn } from "@/lib/utils";
import { useBackendHealth } from "@/lib/hooks/useBackendHealth";

export function BackendStatusBanner() {
  const { data, isError } = useBackendHealth();

  // No banner in the happy path.
  if (data?.engine_state === "ready") return null;

  let message: string;
  let tone: "warning" | "error";
  let Icon = AlertTriangle;

  if (isError || data === undefined) {
    message = "Cannot reach backend.";
    tone = "error";
    Icon = WifiOff;
  } else if (data.engine_state === "warming") {
    message = "Warming up backend...";
    tone = "warning";
    Icon = Loader2;
  } else {
    // engine_state === "unavailable"
    message = data.engine_message
      ? `Backend unavailable: ${data.engine_message}`
      : "Backend unavailable or models missing.";
    tone = "error";
  }

  return (
    <div
      className={cn(
        "border-b text-sm",
        tone === "warning"
          ? "border-amber-500/50 bg-amber-500/10 text-amber-900 dark:text-amber-200"
          : "border-destructive/50 bg-destructive/10 text-destructive",
      )}
      role="status"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-2 px-4 py-2 sm:px-6 lg:px-8">
        <Icon
          className={cn("h-4 w-4 shrink-0", tone === "warning" && "animate-spin")}
        />
        <span>{message}</span>
      </div>
    </div>
  );
}
