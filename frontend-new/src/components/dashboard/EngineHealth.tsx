
import { useState, useEffect } from 'react';
import { db } from '../../firebase'; // Adjust the path as necessary
import { collection, onSnapshot } from 'firebase/firestore';

const EngineHealth = () => {
  const [engineStatus, setEngineStatus] = useState([]);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'engine_health'), (snapshot) => {
      const statusData = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setEngineStatus(statusData);
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h2 className="text-xl font-semibold mb-4">Engine Health</h2>
      <ul>
        {engineStatus.map(engine => (
          <li key={engine.id} className="flex justify-between items-center mb-2">
            <span>{engine.id}</span>
            <span className={`px-2 py-1 rounded-full text-sm ${engine.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`}>
              {engine.status}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default EngineHealth;
