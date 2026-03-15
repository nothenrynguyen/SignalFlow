"use client";

import { useCallback, useEffect, useState } from "react";
import { api, MetricsSummary, MetricsTimeseries } from "@/lib/api";
import { useMetricsSocket } from "@/lib/useWebSocket";
import { StatCard } from "@/components/StatCard";
import { EventTypeChart } from "@/components/EventTypeChart";
import { TimeseriesChart } from "@/components/TimeseriesChart";
import { EventSimulator } from "@/components/EventSimulator";

type Interval = "minute" | "hour" | "day";

export default function DashboardPage() {
  const [summary, setSummary]       = useState<MetricsSummary | null>(null);
  const [timeseries, setTimeseries] = useState<MetricsTimeseries | null>(null);
  const [interval, setInterval]     = useState<Interval>("hour");
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);

  // ── Data fetching ────────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([
        api.getMetricsSummary(),
        api.getMetricsTimeseries(interval),
      ]);
      setSummary(s);
      setTimeseries(t);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [interval]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // ── WebSocket — apply full summary push or re-fetch on any message ────────
  const { connected } = useMetricsSocket(
    useCallback((msg) => {
      if (msg.type === "metrics_update" && msg.data) {
        // Worker pushed a full pre-computed summary — apply it immediately
        setSummary(msg.data);
        // Still refresh timeseries so the chart stays current
        api.getMetricsTimeseries(interval).then(setTimeseries).catch(() => null);
      } else {
        fetchAll();
      }
    }, [fetchAll, interval])
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
        <div className={`live-badge${connected ? " connected" : ""}`}>
          <span className="live-dot" />
          {connected ? "Live" : "Connecting…"}
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
                interval={interval}
                onIntervalChange={(i) => setInterval(i)}
              />
            )}
          </div>

          {/* Event simulator */}
          <EventSimulator onEventSent={fetchAll} />
        </>
      )}
    </main>
  );
}
