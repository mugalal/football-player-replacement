import type { ReactNode } from "react";

import { BackendStatusBanner } from "@/components/common/BackendStatusBanner";
import { Navbar } from "@/components/layout/Navbar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Navbar />
      <BackendStatusBanner />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-border mt-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 text-xs text-muted-foreground flex items-center justify-between">
          <span>Replacement Scout · GP2 methodology</span>
          <span className="font-mono">v0.1.0</span>
        </div>
      </footer>
    </div>
  );
}
