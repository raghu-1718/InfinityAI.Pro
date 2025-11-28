import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { httpsCallable } from 'firebase/functions';
import { functions } from '../firebase';
import { useAppStore } from '../stores/appStore';

// Firebase Functions
const getGeminiAnalysis = httpsCallable(functions, 'getGeminiAnalysis');
const getVertexAiAnalysis = httpsCallable(functions, 'getVertexAiAnalysis');
const getAiSignals = httpsCallable(functions, 'getAiSignals');
const analyzePortfolio = httpsCallable(functions, 'analyzePortfolio');
const syncHoldings = httpsCallable(functions, 'syncHoldings');
const getDhanOverview = httpsCallable(functions, 'getDhanOverview');
const updateDhanAccessToken = httpsCallable(functions, 'updateDhanAccessToken');


export const useGeminiAnalysis = (prompt?: string) => {
  const setAiAnalysisError = useAppStore((state) => state.setAiAnalysisError)
  const setAiAnalysisLoading = useAppStore((state) => state.setAiAnalysisLoading)

  return useQuery({
    queryKey: ['gemini-analysis', prompt],
    queryFn: async () => {
      setAiAnalysisLoading(true)
      try {
        const result = await getGeminiAnalysis({
          prompt: prompt || 'Provide current market analysis for NIFTY and BANKNIFTY',
          context: { timestamp: new Date().toISOString() }
        })
        setAiAnalysisError(null)
        return result.data
      } catch (error: any) {
        console.error('❌ Gemini Analysis Error:', error)
        setAiAnalysisError(error.message || 'Failed to load Gemini analysis')

        // Return fallback data
        return {
          analysis: {
            timestamp: new Date().toISOString(),
            market_sentiment: 'NEUTRAL',
            confidence: 0.5,
            key_insights: [
              'Analysis service temporarily unavailable',
              'Please check back in a few minutes',
              'Using cached market data where available'
            ],
            recommendations: [
              'Monitor market conditions manually',
              'Check engine status in Engines page',
              'Contact support if issues persist'
            ],
            status: 'fallback'
          }
        }
      } finally {
        setAiAnalysisLoading(false)
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    enabled: true
  })
}

export const useVertexAnalysis = (prompt?: string) => {
  const setAiAnalysisError = useAppStore((state) => state.setAiAnalysisError)

  return useQuery({
    queryKey: ['vertex-analysis', prompt],
    queryFn: async () => {
      try {
        const result = await getVertexAiAnalysis({
          prompt: prompt || 'Analyze current market trends and provide predictions',
          context: { timestamp: new Date().toISOString() }
        })
        setAiAnalysisError(null)
        return result.data
      } catch (error: any) {
        console.error('❌ Vertex AI Analysis Error:', error)
        setAiAnalysisError(error.message || 'Failed to load Vertex AI analysis')

        // Return fallback data
        return {
          analysis: {
            timestamp: new Date().toISOString(),
            model_predictions: {
              nifty_direction: 'NEUTRAL',
              probability: 0.5,
              target_range: 'N/A',
              timeframe: 'N/A'
            },
            status: 'fallback'
          }
        }
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
    enabled: true
  })
}

export const useAiSignals = (symbol?: string) => {
  return useQuery({
    queryKey: ['ai-signals', symbol],
    queryFn: async () => {
      try {
        const result = await getAiSignals({ symbol: symbol || 'NIFTY' })
        return result.data
      } catch (error: any) {
        console.error('❌ AI Signals Error:', error)

        // Return fallback signals
        return {
          signals: {
            timestamp: new Date().toISOString(),
            signals: [
              {
                symbol: symbol || 'NIFTY',
                signal: 'NEUTRAL',
                strength: 0.5,
                analysis: 'Service temporarily unavailable',
                status: 'fallback'
              }
            ]
          }
        }
      }
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 1,
    enabled: true
  })
}

export const usePortfolioAnalysis = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const result = await analyzePortfolio({})
      return result.data
    },
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
    }
  })
}

export const useHoldingsSync = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const result = await syncHoldings({})
      return result.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['dhan-overview'] })
    }
  })
}

export const useDhanOverview = () => {
  return useQuery({
    queryKey: ['dhan-overview'],
    queryFn: async () => {
      try {
        const result = await getDhanOverview({})
        return result.data
      } catch (error: any) {
        console.error('❌ Dhan Overview Error:', error)

        // Return fallback data
        return {
          overview: {
            status: 'unavailable',
            message: 'Failed to load Dhan overview. Please check your API credentials.',
            timestamp: new Date().toISOString()
          }
        }
      }
    },
    staleTime: 1 * 60 * 1000, // 1 minute
    retry: 1,
    enabled: true
  })
}

export const useUpdateDhanAccessToken = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (accessToken: string) => {
      const result = await updateDhanAccessToken({ accessToken });
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dhan-overview'] });
      queryClient.invalidateQueries({ queryKey: ['holdings'] });
      alert('Dhan Access Token updated successfully!');
    },
    onError: (error: any) => {
      alert(`Error updating token: ${error.message}`);
    },
  });
};


// Engine status hooks
export const useEngineStatus = () => {
  const updateEngineStatus = useAppStore((state) => state.updateEngineStatus)

  return useQuery({
    queryKey: ['engine-status'],
    queryFn: async () => {
      const engines = [
        { name: 'engine-a', url: 'https://engine-a.infinityai.pro' },
        { name: 'engine-b', url: 'https://engine-b.infinityai.pro' },
        { name: 'engine-c', url: 'https://engine-c.infinityai.pro' },
        // Engine D merged into Engine C (Execution)
      ]

      const statusPromises = engines.map(async (engine) => {
        try {
          const response = await fetch(`${engine.url}/health`, {
            method: 'GET',
            timeout: 5000
          })
          const status = response.ok ? 'online' : 'error'
          updateEngineStatus(engine.name, { status })
          return { [engine.name]: status }
        } catch (error) {
          updateEngineStatus(engine.name, { status: 'offline' })
          return { [engine.name]: 'offline' }
        }
      })

      const results = await Promise.all(statusPromises)
      return Object.assign({}, ...results)
    },
    refetchInterval: 30000, // Check every 30 seconds
    retry: false
  })
}
