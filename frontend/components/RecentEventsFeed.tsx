"use client";

import type { EventRead } from "@/lib/api";

const TYPE_COLORS: Record<string, string> = {
  page_view:     "#6366f1",
  click:         "#f59e0b",
  signup:        "#10b981",
  purchase:      "#3b82f6",
  session_start: "#8b5cf6",
};

function typeColor(eventType: string) {
  return TYPE_COLORS[eventType] ?? "#888";
}

function relativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 5_000)  return "just now";
  if (diff < 60_000) return `${Math.floor(diff / 1_000)}s ago`;
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  return `${Math.floor(diff / 3_600_000)}h ago`;
}

interface Props {
  events: EventRead[];
}

export function RecentEventsFeed({ events }: Props) {
  return (
    <div className="feed-card">
      <div className="feed-header">
        <span className="chart-title">Recent Events</span>
        <span className="feed-count">{events.length} shown</span>
      </div>

      {events.length === 0 ? (
        <p className="feed-empty">Waiting for events…</p>
      ) : (
        <ul className="feed-list">
          {events.map((ev) => (
            <li key={ev.id} className="feed-item">
              <span
                className="feed-type-pill"
                style={{ borderColor: typeColor(ev.event_type), color: typeColor(ev.event_type) }}
              >
                {ev.event_type}
              </span>
              <span className="feed-session">
                {ev.session_id ?? "—"}
              </span>
              <span className="feed-time">{relativeTime(ev.timestamp)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
