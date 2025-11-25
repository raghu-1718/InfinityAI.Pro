import React, { useEffect } from 'react';
import { ErrorBoundary } from './ErrorBoundary';
import { EnhancedAiAnalysis } from './EnhancedAiAnalysis';
import { DhanIntegration } from './DhanIntegration';
import { useWebSocketStore } from '../stores/webSocketStore';
import { useEngineStatus } from '../hooks/useApi';

export const Dashboard: React.FC = () => {
  const { connect, disconnect } = useWebSocketStore();
  useEngineStatus(); // Periodically check engine status

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 bg-gray-50 min-h-screen">
       <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">InfinityAI.Pro Dashboard</h1>
        <p className="text-gray-600 mt-1">Real-time AI-powered trading insights and portfolio management.</p>
      </header>
      <main className="max-w-7xl mx-auto">
        <ErrorBoundary fallback={<p>Error loading AI Analysis.</p>}>
            <EnhancedAiAnalysis />
        </ErrorBoundary>
        <ErrorBoundary fallback={<p>Error loading Dhan Integration.</p>}>
            <DhanIntegration />
        </ErrorBoundary>
      </main>
    </div>
  );
};
