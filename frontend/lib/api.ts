/**
 * Typed HTTP client for the SignalFlow backend API.
 * Base URL is read from the NEXT_PUBLIC_API_URL env variable.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

export interface EventCreate {
  event_type: "page_view" | "click" | "signup" | "purchase" | "session_start" | string;
  user_id?: string;
  session_id: string;
  timestamp?: string; // ISO-8601
  metadata?: Record<string, unknown>;
}

export interface EventRead extends EventCreate {
  id: string;
  timestamp: string;
}

export interface EventTypeCounts {
  event_type: string;
  count: number;
}

export interface MetricsSummary {
  total_events: number;
  unique_sessions: number;
  unique_users: number;
  counts_by_type: EventTypeCounts[];
}

export interface TimeseriesPoint {
  bucket: string;
  count: number;
}

export interface MetricsTimeseries {
  data: TimeseriesPoint[];
}

// ── Helpers ────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── API calls ──────────────────────────────────────────────────────────────

export const api = {
  ingestEvent: (payload: EventCreate) =>
    apiFetch<EventRead>("/events", { method: "POST", body: JSON.stringify(payload) }),

  getMetricsSummary: (lookbackHours?: number) => {
    const qs = lookbackHours != null ? `?lookback_hours=${lookbackHours}` : "";
    return apiFetch<MetricsSummary>(`/metrics/summary${qs}`);
  },

  getMetricsTimeseries: (interval: "minute" | "hour" | "day" = "hour", lookbackHours = 24) =>
    apiFetch<MetricsTimeseries>(`/metrics/timeseries?interval=${interval}&lookback_hours=${lookbackHours}`),
};
