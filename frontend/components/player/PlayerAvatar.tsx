"use client";
import { useState } from "react";

import { AVATAR_PALETTE } from "@/lib/constants";
import { cn, initialsFromName, stableIndex } from "@/lib/utils";

interface PlayerAvatarProps {
  photoUrl?: string | null;
  name: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZE_CLASSES: Record<NonNullable<PlayerAvatarProps["size"]>, string> = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-20 w-20 text-2xl",
};

export function PlayerAvatar({ photoUrl, name, size = "md", className }: PlayerAvatarProps) {
  // Track image-load failures so we can fall back to initials at runtime
  // without an extra HEAD request from the server side.
  const [failed, setFailed] = useState(false);
  const initials = initialsFromName(name);
  const color = AVATAR_PALETTE[stableIndex(name, AVATAR_PALETTE.length)];

  if (photoUrl && !failed) {
    return (
      // We use a plain <img> here because backend photos come from a
      // separate origin (the HF Space) and we don't want to configure
      // next/image domains. This also lets us silently fail to initials.
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={photoUrl}
        alt={name}
        onError={() => setFailed(true)}
        className={cn(
          "rounded-full object-cover ring-1 ring-border",
          SIZE_CLASSES[size],
          className,
        )}
      />
    );
  }

  return (
    <div
      aria-label={name}
      className={cn(
        "inline-flex items-center justify-center rounded-full font-semibold text-white ring-1 ring-border select-none",
        color,
        SIZE_CLASSES[size],
        className,
      )}
    >
      {initials}
    </div>
  );
}
