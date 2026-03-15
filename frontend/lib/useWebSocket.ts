"use client";

import { useEffect, useRef, useState } from "react";
import type { MetricsSummary } from "@/lib/api";

function getWsUrl(): string {
  if (typeof window === "undefined") return "";
  const env = process.env.NEXT_PUBLIC_WS_URL;
  if (env) return env;
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://localhost:8000/ws/metrics`;
}

export interface WsMessage {
  type: string;
  event_type?: string;
  data?: MetricsSummary;
  event?: import("@/lib/api").EventRead;
}

export function useMetricsSocket(onMessage?: (msg: WsMessage) => void) {
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    const url = getWsUrl();
    if (!url) return;

    let ws: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen  = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        reconnectTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data) as WsMessage;
          onMessageRef.current?.(msg);
        } catch {
          // ignore non-JSON frames
        }
      };
    }

    connect();
    return () => {
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  return { connected };
}
