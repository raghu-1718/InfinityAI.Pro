import { useState, useEffect } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';

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
    if (!uid || !isSupabaseConfigured()) return;

    // Fetch audit events from logs table (when configured)
    const fetchEvents = async () => {
      try {
        const { data, error } = await supabase
          .from('logs')
          .select('*')
          .eq('user_id', uid)
          .order('timestamp', { ascending: false })
          .limit(100);

        if (data && !error) {
          const mapped: AuditEvent[] = data.map((row: any) => ({
            uid: row.user_id,
            event: row.type || row.level || 'UNKNOWN',
            details: typeof row.description === 'string'
              ? (() => { try { return JSON.parse(row.description); } catch { return { message: row.description }; } })()
              : row.metadata || {},
            severity: row.severity || row.level,
            timestamp: row.timestamp || row.created_at,
          }));
          setEvents(mapped);
        }
      } catch (err) {
        console.error("Audit Timeline Fetch Error:", err);
      }
    };

    // Initial fetch
    fetchEvents();

    // Poll every 10 seconds
    const interval = setInterval(fetchEvents, 10000);

    return () => clearInterval(interval);
  }, [uid]);

  return events;
}
