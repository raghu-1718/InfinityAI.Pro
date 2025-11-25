import React from 'react';
import { useGeminiAnalysis, useVertexAnalysis, useAiSignals } from '../hooks/useApi';
import { useAppStore } from '../stores/appStore';
import { ErrorBoundary, RetryWrapper } from './ErrorBoundary';

export const EnhancedAiAnalysis: React.FC = () => {
  const { data: geminiData, isLoading: geminiLoading, error: geminiError } = useGeminiAnalysis();
  const { data: vertexData, isLoading: vertexLoading, error: vertexError } = useVertexAnalysis();
  const { data: signalsData, isLoading: signalsLoading, error: signalsError } = useAiSignals();

  const aiAnalysis = useAppStore((state) => state.aiAnalysis);
  const realTimeData = useAppStore((state) => state.realTimeData);

  const isAnyLoading = geminiLoading || vertexLoading || signalsLoading || aiAnalysis.isLoading;
  const hasAnyError = geminiError || vertexError || signalsError || aiAnalysis.error;

  return (
    <ErrorBoundary>
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-800">
            🤖 AI Market Analysis
          </h2>
          <div className="flex items-center space-x-2">
            {realTimeData.websocketConnected && (
              <span className="text-green-500 text-sm">● Live</span>
            )}
            {aiAnalysis.lastUpdated && (
              <span className="text-gray-500 text-sm">
                Updated: {new Date(aiAnalysis.lastUpdated).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>

        {isAnyLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="ml-3 text-gray-600">Loading AI analysis...</span>
          </div>
        )}

        {hasAnyError && !isAnyLoading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div className="flex items-center">
              <span className="text-red-500 text-xl mr-3">⚠️</span>
              <div>
                <h3 className="text-red-800 font-medium">Analysis Service Issues</h3>
                <p className="text-red-600 text-sm mt-1">
                  {aiAnalysis.error || 'Some AI services are temporarily unavailable. Please refresh the page.'}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gemini Analysis */}
          <RetryWrapper>
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
              <h3 className="font-medium text-blue-800 mb-3 flex items-center">
                🧠 Gemini Insights
                {geminiLoading && <div className="ml-2 animate-pulse text-blue-500">●</div>}
              </h3>

              {geminiData?.analysis ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-blue-600">Market Sentiment:</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${{
                      'BULLISH': 'bg-green-100 text-green-800',
                      'BEARISH': 'bg-red-100 text-red-800',
                      'NEUTRAL': 'bg-gray-100 text-gray-800',
                    }[geminiData.analysis.market_sentiment] || 'bg-gray-100 text-gray-800'}`}>
                      {geminiData.analysis.market_sentiment || 'N/A'}
                    </span>
                  </div>

                  {geminiData.analysis.key_insights && (
                    <div>
                      <p className="text-sm text-blue-600 mb-1">Key Insights:</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {geminiData.analysis.key_insights.slice(0, 3).map((insight: string, index: number) => (
                          <li key={index} className="flex items-start">
                            <span className="text-blue-500 mr-2">•</span>
                            {insight}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-blue-600 text-sm">
                  {geminiError ? 'Service temporarily unavailable' : 'Loading insights...'}
                </p>
              )}
            </div>
          </RetryWrapper>

          {/* Vertex AI Analysis */}
          <RetryWrapper>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
              <h3 className="font-medium text-purple-800 mb-3 flex items-center">
                🎯 Vertex AI Predictions
                {vertexLoading && <div className="ml-2 animate-pulse text-purple-500">●</div>}
              </h3>

              {vertexData?.analysis?.model_predictions ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-purple-600">NIFTY Direction:</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${{
                      'UP': 'bg-green-100 text-green-800',
                      'DOWN': 'bg-red-100 text-red-800',
                      'NEUTRAL': 'bg-gray-100 text-gray-800',
                    }[vertexData.analysis.model_predictions.nifty_direction] || 'bg-gray-100 text-gray-800'}`}>
                      {vertexData.analysis.model_predictions.nifty_direction || 'N/A'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-purple-600">Confidence:</span>
                    <span className="text-sm font-medium text-gray-700">
                      {(vertexData.analysis.model_predictions.probability * 100).toFixed(1)}%
                    </span>
                  </div>

                  {vertexData.analysis.model_predictions.target_range && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-purple-600">Target Range:</span>
                      <span className="text-sm font-medium text-gray-700">
                        {vertexData.analysis.model_predictions.target_range}
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-purple-600 text-sm">
                  {vertexError ? 'Service temporarily unavailable' : 'Loading predictions...'}
                </p>
              )}
            </div>
          </RetryWrapper>
        </div>

        {/* AI Signals */}
        <RetryWrapper>
          <div className="mt-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
            <h3 className="font-medium text-green-800 mb-3 flex items-center">
              📊 AI Trading Signals
              {signalsLoading && <div className="ml-2 animate-pulse text-green-500">●</div>}
            </h3>

            {signalsData?.signals?.signals ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {signalsData.signals.signals.slice(0, 4).map((signal: any, index: number) => (
                  <div key={index} className="bg-white rounded-lg p-3 border border-green-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-800">{signal.symbol}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${{
                        'BUY': 'bg-green-100 text-green-800',
                        'SELL': 'bg-red-100 text-red-800',
                        'HOLD': 'bg-yellow-100 text-yellow-800',
                        'NEUTRAL': 'bg-gray-100 text-gray-800',
                      }[signal.signal] || 'bg-gray-100 text-gray-800'}`}>
                        {signal.signal}
                      </span>
                    </div>

                    {signal.strength && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Strength:</span>
                        <span className="font-medium">{(signal.strength * 100).toFixed(0)}%</span>
                      </div>
                    )}

                    {signal.entry_price && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Entry:</span>
                        <span className="font-medium">₹{signal.entry_price}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-green-600 text-sm">
                {signalsError ? 'Service temporarily unavailable' : 'Loading signals...'}
              </p>
            )}
          </div>
        </RetryWrapper>
      </div>
    </ErrorBoundary>
  );
};
