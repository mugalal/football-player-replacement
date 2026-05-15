"use client";
import { Search, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { PlayerAvatar } from "@/components/player/PlayerAvatar";
import { Input } from "@/components/ui/input";
import { usePlayerSearch } from "@/lib/hooks/usePlayerSearch";
import type { PlayerSummary } from "@/lib/types";
import { cn } from "@/lib/utils";

interface PlayerAutocompleteProps {
  onSelect: (player: PlayerSummary) => void;
  placeholder?: string;
  autoFocus?: boolean;
}

export function PlayerAutocomplete({
  onSelect,
  placeholder = "Search players (e.g. Mané, Kane, Modrić)…",
  autoFocus,
}: PlayerAutocompleteProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const debounced = useDebounced(query, 200);
  const { data, isFetching } = usePlayerSearch(debounced, 12);

  // Close dropdown when clicking outside.
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  return (
    <div ref={wrapRef} className="relative">
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          autoFocus={autoFocus}
          placeholder={placeholder}
          className="pl-8 pr-8"
        />
        {query && (
          <button
            aria-label="Clear search"
            onClick={() => {
              setQuery("");
              setOpen(false);
            }}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {open && (data || isFetching) && (
        <div className="absolute z-30 mt-1 w-full rounded-md border border-border bg-popover bg-card shadow-md overflow-hidden">
          {isFetching && !data && (
            <div className="p-3 text-sm text-muted-foreground flex items-center gap-2">
              <LoadingSpinner /> Searching…
            </div>
          )}
          {data && data.length === 0 && (
            <div className="p-3 text-sm text-muted-foreground">
              No matches. Note: engine matching is plain-Unicode — try the
              accented form (e.g. <span className="font-mono">Mané</span>).
            </div>
          )}
          {data && data.length > 0 && (
            <ul role="listbox" className="max-h-80 overflow-auto py-1">
              {data.map((p) => (
                <li key={p.player_id}>
                  <button
                    role="option"
                    aria-selected="false"
                    onClick={() => {
                      onSelect(p);
                      setQuery("");
                      setOpen(false);
                    }}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-accent transition-colors",
                    )}
                  >
                    <PlayerAvatar
                      photoUrl={p.photo_url}
                      name={p.name}
                      size="sm"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">{p.name}</div>
                      <div className="text-xs text-muted-foreground truncate">
                        {p.primary_position} · {p.team}
                      </div>
                    </div>
                    <div className="text-xs font-mono text-muted-foreground shrink-0">
                      {p.num_matches}m
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}
