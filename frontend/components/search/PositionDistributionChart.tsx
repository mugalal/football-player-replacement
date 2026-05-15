"use client";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface PositionDistributionChartProps {
  /** Engine returns {position_name: fraction or count}. */
  distribution: Record<string, number>;
  height?: number;
}

export function PositionDistributionChart({
  distribution,
  height = 220,
}: PositionDistributionChartProps) {
  const data = Object.entries(distribution)
    .map(([position, value]) => ({ position, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No position distribution available.</p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 12, bottom: 4, left: 8 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
        <XAxis
          type="number"
          stroke="hsl(var(--muted-foreground))"
          fontSize={11}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="position"
          stroke="hsl(var(--muted-foreground))"
          fontSize={11}
          width={140}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          cursor={{ fill: "hsl(var(--accent))", opacity: 0.4 }}
          contentStyle={{
            background: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: 6,
            fontSize: 12,
          }}
          formatter={(v: number) => v.toFixed(3)}
        />
        <Bar dataKey="value" fill="hsl(var(--primary))" radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
