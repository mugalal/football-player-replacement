import { PlayerAvatar } from "@/components/player/PlayerAvatar";
import { VersatilityBar } from "@/components/player/VersatilityBar";
import { Card, CardContent } from "@/components/ui/card";
import type { PlayerDetail } from "@/lib/types";

export function PlayerHeader({ player }: { player: PlayerDetail }) {
  return (
    <Card>
      <CardContent className="p-6 flex flex-col sm:flex-row gap-6 items-start">
        <PlayerAvatar
          photoUrl={player.photo_url}
          name={player.name}
          size="lg"
          className="shrink-0"
        />
        <div className="flex-1 min-w-0 space-y-4 w-full">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight truncate">{player.name}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {player.primary_position} · {player.team}
            </p>
          </div>
          <div className="grid grid-cols-3 gap-4 max-w-md">
            <Stat label="Matches" value={String(player.num_matches)} />
            <Stat label="Positions" value={String(player.num_distinct_positions)} />
            <Stat label="ID" value={player.player_id} mono />
          </div>
          <VersatilityBar score={player.versatility_score} />
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
      <div className={`mt-0.5 text-lg ${mono ? "font-mono text-base" : "font-semibold"}`} data-numeric>
        {value}
      </div>
    </div>
  );
}
