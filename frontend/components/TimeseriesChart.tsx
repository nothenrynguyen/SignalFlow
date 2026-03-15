"use client";

import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import type { TimeseriesPoint } from "@/lib/api";

type Interval = "minute" | "hour" | "day";

function formatBucket(iso: string, interval: Interval): string {
  const d = new Date(iso);
  if (interval === "minute") return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (interval === "hour")   return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

interface Props {
  data: TimeseriesPoint[];
  interval: Interval;
}

export function TimeseriesChart({ data, interval }: Props) {
  const chartData = data.map((p) => ({ ...p, label: formatBucket(p.bucket, interval) }));

  return (
    <div className="chart-card">
      <p className="chart-title">Event Volume Over Time</p>
      <ResponsiveContainer width="100%" height={210}>
        <AreaChart data={chartData} margin={{ top: 0, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "#888", fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
          <YAxis tick={{ fill: "#888", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip
            cursor={{ stroke: "#4f46e5", strokeWidth: 1 }}
            contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#e8eaf0" }}
          />
          <Area type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} fill="url(#areaGrad)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
