import { useEngineHealth } from '../hooks/useEngineHealth'

const engines = [
  { key: 'A', service: 'Alpha', healthy: true, status: 'Running' },
  { key: 'B', service: 'Beta', healthy: true, status: 'Running' },
  { key: 'C', service: 'Gamma', healthy: true, status: 'Running' },
  { key: 'D', service: 'Delta', healthy: false, status: 'Error' },
];

export default function Engines() {
  // const { data: engines } = useEngineHealth()

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Engine Management</h1>
      <p className="text-gray-400">Monitor and manage all backend engines</p>

      <div className="grid grid-cols-1 gap-6">
        {engines?.map((engine) => (
          <div key={engine.key} className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-2xl font-bold text-white">Engine {engine.key}</h3>
                <p className="text-gray-400">{engine.service}</p>
              </div>
              <div className={`px-4 py-2 rounded-lg ${
                engine.healthy ? 'bg-green-600' : 'bg-red-600'
              }`}>
                {engine.status}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
