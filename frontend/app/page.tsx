"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, EventRead, MetricsSummary, MetricsTimeseries } from "@/lib/api";
import { useMetricsSocket } from "@/lib/useWebSocket";
import { StatCard } from "@/components/StatCard";
import { EventTypeChart } from "@/components/EventTypeChart";
import { TimeseriesChart } from "@/components/TimeseriesChart";
import { EventSimulator } from "@/components/EventSimulator";
import { RecentEventsFeed } from "@/components/RecentEventsFeed";

type Interval = "minute" | "hour" | "day";

interface TimeRange {
  label: string;
  hours: number;
  interval: Interval;
}

const TIME_RANGES: TimeRange[] = [
  { label: "15m", hours: 0.25,  interval: "minute" },
  { label: "1h",  hours: 1,     interval: "minute" },
  { label: "24h", hours: 24,    interval: "hour"   },
];

export default function DashboardPage() {
  const [summary, setSummary]           = useState<MetricsSummary | null>(null);
  const [timeseries, setTimeseries]     = useState<MetricsTimeseries | null>(null);
  const [timeRange, setTimeRange]       = useState<TimeRange>(TIME_RANGES[2]); // default: 24h
  const [isPaused, setIsPaused]         = useState(false);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState<string | null>(null);
  const [recentEvents, setRecentEvents] = useState<EventRead[]>([]);

  const isPausedRef = useRef(isPaused);
  isPausedRef.current = isPaused;

  // ── Data fetching ────────────────────────────────────────────────────────
  const fetchAll = useCallback(async (range: TimeRange = timeRange) => {
    try {
      const [s, t] = await Promise.all([
        api.getMetricsSummary(range.hours),
        api.getMetricsTimeseries(range.interval, range.hours),
      ]);
      setSummary(s);
      setTimeseries(t);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // ── Time range selection ─────────────────────────────────────────────────
  function selectRange(range: TimeRange) {
    setTimeRange(range);
    setLoading(true);
    fetchAll(range);
  }

  // ── Pause / Resume ───────────────────────────────────────────────────────
  function togglePause() {
    const next = !isPaused;
    setIsPaused(next);
    if (!next) {
      // Resuming — fetch fresh data immediately to catch up
      fetchAll();
    }
  }

  // ── WebSocket — handle metrics push + live event feed ───────────────────
  const { connected } = useMetricsSocket(
    useCallback((msg) => {
      if (isPausedRef.current) return;   // gate updates when paused

      if (msg.type === "event_ingested" && msg.event) {
        setRecentEvents((prev) => [msg.event!, ...prev].slice(0, 20));
      } else if (msg.type === "metrics_update") {
        // Worker always broadcasts all-time summary.
        // Re-fetch if a time filter is active so the numbers stay accurate.
        fetchAll();
      }
    }, [fetchAll])
  );

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <main className="page">
      {/* Header */}
      <div className="header">
        <div className="header-left">
          <h1>SignalFlow</h1>
          <p>Real-Time Event Analytics</p>
        </div>

        <div className="header-controls">
          {/* Time range selector */}
          <div className="range-group">
            {TIME_RANGES.map((r) => (
              <button
                key={r.label}
                className={`range-btn${timeRange.label === r.label ? " active" : ""}`}
                onClick={() => selectRange(r)}
              >
                {r.label}
              </button>
            ))}
          </div>

          {/* Pause / Resume toggle */}
          <button
            className={`pause-btn${isPaused ? " paused" : ""}`}
            onClick={togglePause}
          >
            {isPaused ? "▶ Resume" : "⏸ Pause"}
          </button>

          {/* Live badge */}
          <div className={`live-badge${connected && !isPaused ? " connected" : ""}`}>
            <span className="live-dot" />
            {isPaused ? "Paused" : connected ? "Live" : "Connecting…"}
          </div>
        </div>
      </div>

      {/* KPI cards */}
      {loading && <div className="loading-state">Loading…</div>}
      {error   && <div className="error-state">{error}</div>}

      {summary && !loading && (
        <>
          <div className="stat-grid">
            <StatCard label="Total Events"    value={summary.total_events.toLocaleString()} />
            <StatCard label="Unique Sessions" value={summary.unique_sessions.toLocaleString()} />
            <StatCard label="Unique Users"    value={summary.unique_users.toLocaleString()} />
            {summary.counts_by_type[0] && (
              <StatCard
                label="Top Event"
                value={summary.counts_by_type[0].event_type}
                sub={`${summary.counts_by_type[0].count} events`}
              />
            )}
          </div>

          {/* Charts */}
          <div className="chart-grid">
            <EventTypeChart data={summary.counts_by_type} />
            {timeseries && (
              <TimeseriesChart
                data={timeseries.data}
                interval={timeRange.interval}
              />
            )}
          </div>

          {/* Event simulator */}
          <EventSimulator onEventSent={() => fetchAll()} />

          {/* Live event feed */}
          <RecentEventsFeed events={recentEvents} />
        </>
      )}
    </main>
  );
}
