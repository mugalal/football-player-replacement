import { ArrowRight, Boxes, Layers, Sparkles, Target, UserPlus, Users, Zap } from "lucide-react";
import Link from "next/link";

import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/badge";

interface Scenario {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  hint: string;
}

const SCENARIOS: Scenario[] = [
  {
    title: "Replace a player",
    description: "Pick one source player and find the closest match in the dataset, with optional profile upgrades.",
    href: "/replace",
    icon: UserPlus,
    hint: "Single source · 1 click",
  },
  {
    title: "Scouting brief",
    description: "Pool several sources into one target profile. Ideal for replacing a role, not just a name.",
    href: "/brief",
    icon: Users,
    hint: "Multi-source · weighted",
  },
  {
    title: "Mané validation",
    description: "Given Liverpool's 2015-16 attackers + Klopp upgrades, the methodology recovers Sadio Mané.",
    href: "/validations/mane",
    icon: Sparkles,
    badge: "Locked regression",
    hint: "Cached after first run",
  },
];

const HOW_IT_WORKS: { icon: React.ComponentType<{ className?: string }>; title: string; body: string }[] = [
  {
    icon: Layers,
    title: "On-ball + off-ball split",
    body: "Separate Doc2Vec corpora preserve information that token-level mixing throws away.",
  },
  {
    icon: Boxes,
    title: "Player2Vec embeddings",
    body: "Per-match vectors averaged into a 64-d player representation used for similarity search.",
  },
  {
    icon: Zap,
    title: "Profile interventions",
    body: "Modify a source's tokens (cut-inside, finishing, pressing…) and re-infer to nudge the target.",
  },
];

export default function HomePage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-14">
        {/* HERO */}
        <header className="max-w-3xl">
          <div className="flex items-center gap-2 mb-5">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/5 px-2.5 py-1 text-[11px] font-medium text-primary uppercase tracking-wider">
              <Target className="h-3 w-3" />
              GP2 methodology
            </span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-[1.05]">
            Find the right replacement,
            <br />
            <span className="text-primary">not just the closest name.</span>
          </h1>
          <p className="mt-5 text-base text-muted-foreground leading-relaxed">
            A football scouting tool built on on-ball / off-ball player-match
            embeddings. Search across ~2,200 players, pool multiple sources
            into a single target profile, and apply Klopp-style upgrades —
            with a locked historical regression that recovers
            Liverpool&apos;s actual 2016 signing of Sadio Mané.
          </p>
        </header>

        {/* SCENARIO CARDS */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-3">
          {SCENARIOS.map((s) => (
            <Link
              key={s.href}
              href={s.href}
              className="group relative rounded-lg border border-border bg-card p-5 transition-all hover:border-primary/40 hover:bg-card/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <div className="flex items-start justify-between">
                <div className="rounded-md bg-primary/10 p-2 text-primary ring-1 ring-primary/20">
                  <s.icon className="h-5 w-5" />
                </div>
                {s.badge && (
                  <Badge variant="secondary" className="text-[10px] uppercase tracking-wider">
                    {s.badge}
                  </Badge>
                )}
              </div>
              <h3 className="mt-5 text-base font-semibold tracking-tight">{s.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">
                {s.description}
              </p>
              <div className="mt-5 flex items-center justify-between border-t border-border/60 pt-3 text-xs">
                <span className="font-mono text-muted-foreground" data-numeric>
                  {s.hint}
                </span>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
              </div>
            </Link>
          ))}
        </div>

        {/* HOW IT WORKS */}
        <section className="mt-20">
          <div className="flex items-baseline justify-between mb-6">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              How it works
            </h2>
            <Link
              href="/validations/mane"
              className="text-xs text-muted-foreground hover:text-primary transition-colors"
            >
              See the validation →
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {HOW_IT_WORKS.map((step, i) => (
              <div
                key={step.title}
                className="relative rounded-lg border border-border bg-card/50 p-5"
              >
                <div className="flex items-center justify-between">
                  <step.icon className="h-4 w-4 text-primary" />
                  <span className="font-mono text-[10px] text-muted-foreground" data-numeric>
                    0{i + 1}
                  </span>
                </div>
                <h4 className="mt-4 text-sm font-semibold">{step.title}</h4>
                <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                  {step.body}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
