
import { useState, useEffect } from 'react';
import { db } from '../firebase'; // Adjust the path as necessary
import { collection, onSnapshot, query, orderBy, limit } from 'firebase/firestore';

const TradeLog = () => {
  const [trades, setTrades] = useState([]);

  useEffect(() => {
    const q = query(collection(db, 'trades'), orderBy('timestamp', 'desc'), limit(20));
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const tradesData = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setTrades(tradesData);
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="bg-gray-800 p-4 rounded-lg mt-4">
      <h2 class="text-xl font-semibold mb-4">Trade Log</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-400 uppercase bg-gray-700">
            <tr>
              <th scope="col" className="px-6 py-3">Symbol</th>
              <th scope="col" className="px-6 py-3">Action</th>
              <th scope="col" className="px-6 py-3">Quantity</th>
              <th scope="col" className="px-6 py-3">Price</th>
              <th scope="col" className="px-6 py-3">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {trades.map(trade => (
              <tr key={trade.id} className="border-b border-gray-700">
                <td className="px-6 py-4">{trade.symbol}</td>
                <td className="px-6 py-4">{trade.action}</td>
                <td className="px-6 py-4">{trade.quantity}</td>
                <td className="px-6 py-4">{trade.price}</td>
                <td className="px-6 py-4">{new Date(trade.timestamp.seconds * 1000).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TradeLog;
