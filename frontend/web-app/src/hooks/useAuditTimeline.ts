import { useState, useEffect } from 'react';
import { getEngineCUrl } from '@/lib/api';

export interface AuditEvent {
  uid: string;
  event: string;
  details: Record<string, any>;
  severity?: string;
  timestamp: string;
}

export function useAuditTimeline(uid: string | null | undefined) {
  const [events, setEvents] = useState<AuditEvent[]>([]);

  useEffect(() => {
    if (!uid) return;

    // Fetch audit and system telemetry from Engine-C
    const fetchEvents = async () => {
      try {
        const engineCUrl = getEngineCUrl();
        const res = await fetch(`${engineCUrl}/api/system/status`, {
          headers: { 'X-User-ID': uid },
        });
        if (res.ok) {
          const data = await res.json();
          const currentEvents: AuditEvent[] = [
            {
              uid: uid,
              event: 'SYSTEM_TELEMETRY',
              details: {
                dhan_connected: data.dhan_connected,
                system_status: data.system_status,
                account: data.account_name || 'Active Trader',
              },
              severity: data.dhan_connected ? 'success' : 'info',
              timestamp: data.timestamp || new Date().toISOString(),
            },
          ];
          setEvents(currentEvents);
        }
      } catch (err) {
        // Safe non-blocking fallback
      }
    };

    // Initial fetch
    fetchEvents();

    // Poll every 20 seconds
    const interval = setInterval(fetchEvents, 20000);

    return () => clearInterval(interval);
  }, [uid]);

  return events;
}

