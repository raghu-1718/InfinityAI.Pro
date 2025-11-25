import React, { useState } from 'react';
import { useUpdateDhanAccessToken } from '../hooks/useApi';

export const DhanIntegration: React.FC = () => {
  const [accessToken, setAccessToken] = useState('');
  const updateTokenMutation = useUpdateDhanAccessToken();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken.trim()) {
      alert('Please enter an access token.');
      return;
    }
    updateTokenMutation.mutate(accessToken);
  };

  const redirectUrl = 'https://infinityai.pro/auth/dhan/callback';
  const postbackUrl = 'https://infinityai.pro/api/webhooks/dhan';

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mt-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        🔗 Dhan Broker Integration
      </h2>
      <div className="space-y-4">
        <div>
          <h3 className="font-medium text-gray-700">Configuration URLs</h3>
          <div className="mt-2 space-y-2 text-sm">
            <div className="flex items-center justify-between bg-gray-50 p-3 rounded-lg border">
              <span className="text-gray-600">Redirect URL:</span>
              <code className="font-mono text-gray-800 bg-gray-200 px-2 py-1 rounded">{redirectUrl}</code>
            </div>
            <div className="flex items-center justify-between bg-gray-50 p-3 rounded-lg border">
              <span className="text-gray-600">Postback URL:</span>
              <code className="font-mono text-gray-800 bg-gray-200 px-2 py-1 rounded">{postbackUrl}</code>
            </div>
          </div>
           <p className="text-xs text-gray-500 mt-2">Use these URLs in the Dhan developer portal to configure your application.</p>
        </div>

        <div>
          <h3 className="font-medium text-gray-700">Update Access Token</h3>
           <p className="text-xs text-gray-500 mb-2">Update your daily access token here. Your API Key and Secret are stored securely in GCP Secret Manager.</p>
          <form onSubmit={handleSubmit} className="flex items-center space-x-2">
            <input
              type="password"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              placeholder="Enter daily access token"
              className="flex-grow p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              disabled={updateTokenMutation.isPending}
            />
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
              disabled={updateTokenMutation.isPending}
            >
              {updateTokenMutation.isPending ? 'Updating...' : 'Update Token'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
