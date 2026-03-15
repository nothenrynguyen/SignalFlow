"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { randomSessionId } from "@/lib/utils";

const EVENT_TYPES = ["page_view", "click", "signup", "purchase", "session_start"] as const;

interface Props { onEventSent?: () => void }

export function EventSimulator({ onEventSent }: Props) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus]   = useState<{ text: string; error: boolean } | null>(null);

  async function sendEvent(eventType: string) {
    setLoading(true);
    setStatus(null);
    try {
      await api.ingestEvent({
        event_type: eventType,
        session_id: randomSessionId(),
        user_id: `demo-user-${Math.floor(Math.random() * 20)}`,
      });
      setStatus({ text: `✓ Sent: ${eventType}`, error: false });
      onEventSent?.();
    } catch (err) {
      setStatus({ text: `Error: ${String(err)}`, error: true });
    } finally {
      setLoading(false);
    }
  }

  async function sendBurst() {
    setLoading(true);
    setStatus(null);
    try {
      await Promise.all(
        Array.from({ length: 10 }, () =>
          api.ingestEvent({
            event_type: EVENT_TYPES[Math.floor(Math.random() * EVENT_TYPES.length)],
            session_id: randomSessionId(),
            user_id: `demo-user-${Math.floor(Math.random() * 20)}`,
          })
        )
      );
      setStatus({ text: "✓ Sent 10 random events", error: false });
      onEventSent?.();
    } catch (err) {
      setStatus({ text: `Error: ${String(err)}`, error: true });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="simulator-card">
      <p className="chart-title">Event Simulator</p>
      <div className="btn-row">
        {EVENT_TYPES.map((type) => (
          <button key={type} className="btn" onClick={() => sendEvent(type)} disabled={loading}>
            {type}
          </button>
        ))}
        <button className="btn btn-primary" onClick={sendBurst} disabled={loading}>
          Burst ×10
        </button>
      </div>
      {status && (
        <p className={`status-msg${status.error ? " error" : ""}`}>{status.text}</p>
      )}
    </div>
  );
}
