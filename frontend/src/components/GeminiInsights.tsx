/**
 * GeminiInsights Component
 * 
 * Displays real-time AI analysis from Gemini extension
 * Listens to Firestore 'generate' collection for latest insights
 */

import { useEffect, useState } from "react";
import { db } from "../firebaseConfig";
import { 
  collection, 
  query, 
  orderBy, 
  limit, 
  onSnapshot,
  QuerySnapshot,
  DocumentData 
} from "firebase/firestore";

interface GeminiInsightsProps {
  userId: string;
}

interface InsightData {
  output?: string;
  prompt?: string;
  status?: string;
  createTime?: any;
  updateTime?: any;
}

export default function GeminiInsights({ userId }: GeminiInsightsProps) {
  const [insights, setInsights] = useState<string>("Loading AI analysis...");
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    // Query the 'generate' collection for latest AI insights
    const q = query(
      collection(db, "generate"),
      orderBy("updateTime", "desc"),
      limit(1)
    );

    const unsubscribe = onSnapshot(
      q,
      (snapshot: QuerySnapshot<DocumentData>) => {
        if (!snapshot.empty) {
          const latestDoc = snapshot.docs[0];
          const data = latestDoc.data() as InsightData;

          if (data.output) {
            setInsights(data.output);
            setLastUpdated(new Date());
            setLoading(false);
            setError("");
            console.log("✅ Gemini insights updated:", latestDoc.id);
          } else if (data.status === "PROCESSING") {
            setInsights("🤖 Gemini AI is analyzing market data...");
            setLoading(true);
          } else {
            setInsights("Waiting for AI analysis...");
            setLoading(false);
          }
        } else {
          setInsights("No AI insights available yet. Start a trading session to generate analysis.");
          setLoading(false);
        }
      },
      (err) => {
        console.error("❌ Error listening to Gemini insights:", err);
        setError("Failed to load AI insights. Please refresh the page.");
        setLoading(false);
      }
    );

    return () => unsubscribe();
  }, [userId]);

  return (
    <div className="gemini-insights-container">
      <div className="insights-header">
        <h3>🤖 Gemini AI Analysis</h3>
        {lastUpdated && (
          <span className="last-updated">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="insights-loading">
          <div className="spinner"></div>
          <p>Analyzing market conditions...</p>
        </div>
      ) : (
        <div className="insights-content">
          <pre>{insights}</pre>
        </div>
      )}

      <div className="insights-footer">
        <p className="disclaimer">
          ℹ️ AI analysis is provided for informational purposes only and should not be
          considered as financial advice. Always do your own research.
        </p>
      </div>
    </div>
  );
}
