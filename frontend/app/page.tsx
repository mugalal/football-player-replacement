import { Sparkles, UserPlus, Users } from "lucide-react";
import Link from "next/link";

import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";

interface Scenario {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const SCENARIOS: Scenario[] = [
  {
    title: "Replace a player",
    description: "Pick a single source player and find similar (or upgraded) candidates.",
    href: "/replace",
    icon: UserPlus,
  },
  {
    title: "Scouting brief",
    description: "Pool multiple sources into a target profile and search for who fits.",
    href: "/brief",
    icon: Users,
  },
  {
    title: "Reproduce the Mané validation",
    description:
      "The locked regression check: given Liverpool's 2015-16 attackers and Klopp-style upgrades, the methodology recovers Sadio Mané.",
    href: "/validations/mane",
    icon: Sparkles,
    badge: "Validation",
  },
];

export default function HomePage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight">Replacement Scout</h1>
          <p className="mt-3 text-muted-foreground leading-relaxed">
            A football player replacement tool built on the GP2 methodology — on-ball and
            off-ball player-match embeddings with a documented historical regression that
            recovers Liverpool&apos;s actual 2016 signing of Sadio Mané.
          </p>
        </div>

        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
          {SCENARIOS.map((s) => (
            <Link key={s.href} href={s.href} className="group focus:outline-none">
              <Card className="h-full transition-colors group-hover:border-primary/50 group-focus-visible:ring-2 group-focus-visible:ring-ring">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div className="rounded-md bg-primary/10 p-2 text-primary">
                      <s.icon className="h-5 w-5" />
                    </div>
                    {s.badge && (
                      <Badge variant="secondary" className="text-[10px]">
                        {s.badge}
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="mt-4 text-base">{s.title}</CardTitle>
                  <CardDescription className="mt-1.5">{s.description}</CardDescription>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
