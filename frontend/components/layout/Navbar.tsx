"use client";
import Link from "next/link";

import { ThemeToggle } from "@/components/layout/ThemeToggle";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="font-semibold tracking-tight text-foreground hover:text-primary transition-colors"
        >
          Replacement Scout
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <Link
            href="/replace"
            className="rounded-md px-3 py-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            Replace
          </Link>
          <Link
            href="/brief"
            className="rounded-md px-3 py-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            Brief
          </Link>
          <Link
            href="/validations/mane"
            className="rounded-md px-3 py-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            Validation
          </Link>
          <span className="mx-1 h-5 w-px bg-border" />
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
