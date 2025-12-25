import { useState, useEffect } from 'react';
import { collection, query, where, orderBy, onSnapshot } from "firebase/firestore";
import { db } from "@/lib/firebase";

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
    if (!uid || !db) return;

    const q = query(
      collection(db, "trade_audit"),
      where("uid", "==", uid),
      orderBy("timestamp", "desc")
      // limit(100) // Optional optimization
    );

    const unsubscribe = onSnapshot(q, (snap) => {
      const data = snap.docs.map(d => d.data() as AuditEvent);
      setEvents(data);
    }, (err) => {
        console.error("Audit Stream Error:", err);
    });

    return () => unsubscribe();
  }, [uid]);

  return events;
}
