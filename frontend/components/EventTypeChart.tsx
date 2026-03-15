"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from "recharts";
import type { EventTypeCounts } from "@/lib/api";

const COLORS: Record<string, string> = {
  page_view:     "#6366f1",
  click:         "#8b5cf6",
  signup:        "#10b981",
  purchase:      "#f59e0b",
  session_start: "#3b82f6",
};

interface Props { data: EventTypeCounts[] }

export function EventTypeChart({ data }: Props) {
  return (
    <div className="chart-card">
      <p className="chart-title">Events by Type</p>
      <ResponsiveContainer width="100%" height={210}>
        <BarChart data={data} margin={{ top: 0, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" vertical={false} />
          <XAxis dataKey="event_type" tick={{ fill: "#888", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#888", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip
            cursor={{ fill: "#ffffff08" }}
            contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#e8eaf0" }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.event_type} fill={COLORS[entry.event_type] ?? "#6366f1"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
