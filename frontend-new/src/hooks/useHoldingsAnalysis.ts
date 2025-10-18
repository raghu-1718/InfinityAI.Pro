import { useQuery } from '@tanstack/react-query'
import { ENGINE_C_URL } from '../utils/constants'

interface HoldingItem {
  symbol: string
  qty: number
  avg_price: number
  ltp: number
  invested: number
  current_value: number
  pnl: number
  pnl_pct: number
  type: 'holding' | 'position'
  side?: string
}

interface AnalysisSummary {
  total_invested: number
  total_current: number
  overall_pnl: number
  overall_pct: number
}

interface HoldingsAnalysisData {
  status: string
  funds: any
  summary: AnalysisSummary
  holdings: HoldingItem[]
  positions: HoldingItem[]
  top_gainers: HoldingItem[]
  top_losers: HoldingItem[]
  insights: string[]
  timestamp: string
}

export const useHoldingsAnalysis = () => {
  return useQuery<HoldingsAnalysisData>({
    queryKey: ['holdings-analysis'],
    queryFn: async () => {
      const response = await fetch(`${ENGINE_C_URL}/api/dhan/holdings/analysis`)
      if (!response.ok) throw new Error('Failed to fetch holdings analysis')
      const data = await response.json()
      
      // Also fetch live positions (active trades) from Dhan
      try {
        const positionsResponse = await fetch(`${ENGINE_C_URL}/api/portfolio`)
        if (positionsResponse.ok) {
          const portfolioData = await positionsResponse.json()
          
          // Normalize positions data from Dhan
          if (portfolioData.data?.positions && Array.isArray(portfolioData.data.positions)) {
            const positions: HoldingItem[] = portfolioData.data.positions.map((pos: any) => ({
              symbol: pos.tradingSymbol || pos.symbol || '?',
              qty: pos.quantity || pos.netQty || 0,
              avg_price: pos.avgPrice || pos.buyAvg || 0,
              ltp: pos.ltp || pos.lastTradedPrice || 0,
              invested: (pos.quantity || 0) * (pos.avgPrice || pos.buyAvg || 0),
              current_value: (pos.quantity || 0) * (pos.ltp || 0),
              pnl: pos.realizedProfit || pos.unrealizedProfit || 0,
              pnl_pct: pos.profitPercentage || 0,
              type: 'position' as const,
              side: pos.positionType || pos.productType || 'INTRADAY'
            }))
            
            // Add positions to holdings list with type marker
            data.positions = positions
            
            // Update summary with positions included
            const positionsInvested = positions.reduce((sum, p) => sum + p.invested, 0)
            const positionsCurrent = positions.reduce((sum, p) => sum + p.current_value, 0)
            
            data.summary.total_invested += positionsInvested
            data.summary.total_current += positionsCurrent
            data.summary.overall_pnl = data.summary.total_current - data.summary.total_invested
            data.summary.overall_pct = data.summary.total_invested > 0 
              ? (data.summary.overall_pnl / data.summary.total_invested * 100) 
              : 0
          }
        }
      } catch (posError) {
        console.warn('Could not fetch positions:', posError)
        data.positions = []
      }
      
      return data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 15000
  })
}
