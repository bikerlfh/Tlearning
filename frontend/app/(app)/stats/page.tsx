"use client";

import { useQuery } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { StatusBadge, TypeBadge } from "@/components/Badges";

interface Stats {
  due_today: number;
  studied_today: number;
  streak_days: number;
  total_learned: number;
  heatmap: Array<{ date: string; reviews: number }>;
  retention_curve: Array<{ review_number: number; rate: number; samples: number }>;
  type_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
}

function heatColor(count: number, max: number): string {
  if (count === 0) return "bg-slate-100";
  const ratio = max > 0 ? count / max : 0;
  if (ratio < 0.2) return "bg-indigo-200";
  if (ratio < 0.4) return "bg-indigo-300";
  if (ratio < 0.6) return "bg-indigo-400";
  if (ratio < 0.8) return "bg-indigo-500";
  return "bg-indigo-600";
}

function Kpi({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <Card className="p-4">
      <div className="text-xs uppercase text-slate-500">{label}</div>
      <div className={`text-3xl font-bold ${accent ?? "text-slate-800"}`}>{value}</div>
    </Card>
  );
}

export default function StatsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: () => api.get<Stats>("/api/v1/reviews/stats"),
  });

  if (isLoading || !data) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  const maxReviews = Math.max(...data.heatmap.map((c) => c.reviews), 0);
  const typeEntries = Object.entries(data.type_distribution).sort(
    (a, b) => b[1] - a[1],
  );
  const statusEntries = Object.entries(data.status_distribution).sort(
    (a, b) => b[1] - a[1],
  );

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Stats</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Due today" value={data.due_today} accent="text-indigo-600" />
        <Kpi label="Studied today" value={data.studied_today} accent="text-green-600" />
        <Kpi label="Streak" value={`${data.streak_days}d`} accent="text-orange-600" />
        <Kpi label="Learned" value={data.total_learned} accent="text-slate-800" />
      </div>

      <Card className="p-4 space-y-3">
        <h2 className="font-bold">Last 90 days</h2>
        <div className="grid grid-flow-col grid-rows-7 gap-1">
          {data.heatmap.map((cell) => (
            <div
              key={cell.date}
              className={`w-3 h-3 rounded-sm ${heatColor(cell.reviews, maxReviews)}`}
              title={`${cell.date}: ${cell.reviews} reviews`}
            />
          ))}
        </div>
        <p className="text-xs text-slate-500">
          Each square is one day. Darker = more reviews.
        </p>
      </Card>

      <Card className="p-4 space-y-3">
        <h2 className="font-bold">Retention by review number</h2>
        {data.retention_curve.length === 0 ? (
          <p className="text-sm text-slate-500">
            Not enough reviews yet. Study a few cards to populate this chart.
          </p>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={data.retention_curve.map((d) => ({
                  ...d,
                  rate_pct: Math.round(d.rate * 100),
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="review_number" label={{ value: "Nth review", position: "bottom", offset: -2 }} />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  formatter={(value, name, ctx) => {
                    const samples =
                      (ctx as unknown as { payload?: { samples?: number } })?.payload?.samples ?? 0;
                    if (name === "rate_pct") {
                      return [`${value}% (n=${samples})`, "Success rate"] as [
                        string,
                        string,
                      ];
                    }
                    return [String(value), String(name)] as [string, string];
                  }}
                  labelFormatter={(label) => `Review #${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="rate_pct"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <div className="grid md:grid-cols-2 gap-3">
        <Card className="p-4 space-y-2">
          <h2 className="font-bold">By type</h2>
          {typeEntries.length === 0 ? (
            <p className="text-sm text-slate-500">No artifacts yet.</p>
          ) : (
            typeEntries.map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <TypeBadge type={type} />
                <span className="text-sm font-medium">{count}</span>
              </div>
            ))
          )}
        </Card>
        <Card className="p-4 space-y-2">
          <h2 className="font-bold">By status</h2>
          {statusEntries.length === 0 ? (
            <p className="text-sm text-slate-500">No artifacts yet.</p>
          ) : (
            statusEntries.map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <StatusBadge status={status} />
                <span className="text-sm font-medium">{count}</span>
              </div>
            ))
          )}
        </Card>
      </div>

      <p className="text-xs text-slate-400 text-right">
        Window: {format(parseISO(data.heatmap[0]?.date ?? new Date().toISOString()), "MMM d")} —{" "}
        {format(parseISO(data.heatmap[data.heatmap.length - 1]?.date ?? new Date().toISOString()), "MMM d")}
      </p>
    </div>
  );
}
