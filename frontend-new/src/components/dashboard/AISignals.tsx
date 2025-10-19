
import { useState, useEffect } from 'react';
import { db } from '../../firebase'; // Adjust the path as necessary
import { collection, onSnapshot, query, orderBy, limit } from 'firebase/firestore';

interface Signal {
  id: string;
  signal: string;
  symbol: string;
  timestamp: { seconds: number };
}

const AISignals = () => {
  const [signals, setSignals] = useState<Signal[]>([]);

  useEffect(() => {
    const q = query(collection(db, 'ai_signals'), orderBy('timestamp', 'desc'), limit(10));
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const signalsData = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })) as Signal[];
      setSignals(signalsData);
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="bg-gray-800 p-4 rounded-lg mt-4">
      <h2 className="text-xl font-semibold mb-4">AI Signals</h2>
      <ul>
        {signals.map(signal => (
          <li key={signal.id} className="mb-2">
            <span className="font-bold">{signal.signal}</span> on {signal.symbol} at {new Date(signal.timestamp.seconds * 1000).toLocaleString()}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default AISignals;
