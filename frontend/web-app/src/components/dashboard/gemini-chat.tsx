'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { engineB } from '@/lib/api';
import {
  Sparkles,
  Send,
  Loader2,
  Bot,
  User,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
  RefreshCw,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  data?: unknown;
}

interface GeminiChatProps {
  className?: string;
  expanded?: boolean;
  onToggleExpand?: () => void;
}

// Quick action suggestions
const quickActions = [
  { label: 'NIFTY Analysis', query: 'Analyze NIFTY 50 current trend and key levels' },
  { label: 'RELIANCE Signal', query: 'Give me a trading signal for RELIANCE' },
  { label: 'Bank NIFTY Options', query: 'What options strategy for Bank NIFTY if market is bullish?' },
  { label: 'Risk Check', query: 'How to manage risk in F&O trading?' },
  { label: 'Market Outlook', query: 'What is the market outlook for this week?' },
];

export function GeminiChat({ className, expanded = false, onToggleExpand }: GeminiChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your AI trading assistant powered by Gemini. Ask me anything about stocks, options, market analysis, or trading strategies. I specialize in Indian markets (NSE/BSE).",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (query?: string) => {
    const question = query || input.trim();
    if (!question || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      // Determine if it's a specific request
      const lowerQuery = question.toLowerCase();

      let response;

      if (lowerQuery.includes('signal') || lowerQuery.includes('buy') || lowerQuery.includes('sell')) {
        // Extract symbol from query
        const symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT', 'NIFTY', 'BANKNIFTY'];
        const foundSymbol = symbols.find(s => lowerQuery.toUpperCase().includes(s)) || 'RELIANCE';

        response = await engineB.getFinanceAISignal({
          symbol: foundSymbol,
          current_price: 0, // Backend will fetch
          model_type: 'stock_analyst',
        });
      } else if (lowerQuery.includes('options') || lowerQuery.includes('strategy')) {
        const isNifty = lowerQuery.includes('nifty');
        const isBankNifty = lowerQuery.includes('bank');
        const outlook = lowerQuery.includes('bullish') ? 'BULLISH' : lowerQuery.includes('bearish') ? 'BEARISH' : 'NEUTRAL';

        response = await engineB.getFinanceAIOptionsStrategy({
          index: isBankNifty ? 'BANKNIFTY' : 'NIFTY',
          spot_price: 0, // Backend resolves from live broker feed
          outlook: outlook as any,
          capital: 200000,
          risk_appetite: 'MODERATE',
        });
      } else if (lowerQuery.includes('analysis') || lowerQuery.includes('analyze') || lowerQuery.includes('trend')) {
        const symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'NIFTY', 'BANKNIFTY'];
        const foundSymbol = symbols.find(s => lowerQuery.toUpperCase().includes(s)) || 'NIFTY';

        response = await engineB.getFinanceAIMarketAnalysis({
          symbol: foundSymbol,
          current_price: 0, // Backend will fetch
        });
      } else {
        // General question - use Gemini chat
        response = await engineB.askGemini({ question });
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: formatResponse(response),
        timestamp: new Date(),
        data: response,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || 'Failed to get response');
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${msg || 'Unknown error'}. Please try again.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatResponse = (response: unknown): string => {
    if (!response) return 'No response received.';
    const r = response as any;

    // Signal response
    if (r.signal) {
      const s = r.signal;
      return `## ${r.symbol} Trading Signal

**Action:** ${s.action} ${s.action === 'BUY' ? '🟢' : s.action === 'SELL' ? '🔴' : '🟡'}
**Confidence:** ${((s.confidence ?? 0) * 100).toFixed(0)}%

### Entry & Targets
- **Entry:** ₹${s.entry_price?.toFixed(2) ?? 'Market'}
- **Stop Loss:** ₹${s.stop_loss?.toFixed(2) ?? 'N/A'}
- **Target 1:** ₹${s.target_1?.toFixed(2) ?? 'N/A'}
- **Target 2:** ₹${s.target_2?.toFixed(2) ?? 'N/A'}

### Risk Assessment
- **Risk/Reward:** ${s.risk_reward_ratio?.toFixed(2) ?? 'N/A'}
- **Risk Level:** ${s.risk_level ?? 'MEDIUM'}
- **Timeframe:** ${s.timeframe ?? 'SWING'}

### Reasoning
${r?.reasoning ?? 'Based on technical and fundamental analysis.'}`;
    }

    // Market analysis response
    if (r?.analysis) {
      const a = r.analysis;
      return `## ${r.symbol ?? 'Unknown'} Market Analysis

**Trend:** ${a.trend ?? 'NEUTRAL'} ${a.trend === 'BULLISH' ? '📈' : a.trend === 'BEARISH' ? '📉' : '➡️'}
**Strength:** ${(((a.trend_strength ?? 0) ) * 100).toFixed(0)}%

### Key Levels
- **Support:** ${a.support_levels?.map((l: number) => `₹${l}`).join(', ') || 'N/A'}
- **Resistance:** ${a.resistance_levels?.map((l: number) => `₹${l}`).join(', ') || 'N/A'}

### Technical Indicators
${a.key_indicators ? Object.entries(a.key_indicators).map(([k, v]) => `- **${k.toUpperCase()}:** ${v}`).join('\n') : 'N/A'}

### Volume Analysis
${a.volume_analysis || 'N/A'}

### Recommendation
${r.recommendation ?? 'Monitor the stock for entry opportunities.'}`;
    }

    // Options strategy response
    if (r?.strategy) {
      const s = r.strategy;
      return `## ${r.index ?? r.symbol ?? 'Unknown'} Options Strategy

**Strategy:** ${s.strategy_name ?? 'Strategy'} ${r.outlook === 'BULLISH' ? '📈' : r.outlook === 'BEARISH' ? '📉' : '➡️'}
**Spot Price:** ₹${r.spot_price ?? 'N/A'}

### Strategy Details
${s.strategy_description || ''}

### Legs
${s.legs?.map((leg: any, i: number) => `
**Leg ${i + 1}:**
- ${leg.type} ${leg.option_type} ${leg.strike_price}
- Premium: ₹${leg.entry_price} × ${leg.quantity} lots
- Total: ₹${leg.total_premium}`).join('\n') || 'N/A'}

### Risk/Reward
- **Max Profit:** ₹${s.max_profit || 'N/A'}
- **Max Loss:** ₹${s.max_loss || 'N/A'}
- **Breakeven:** ₹${s.breakeven_point || 'N/A'}`;
    }

    // Risk analysis response
    if (r?.risk_analysis) {
      return `## Portfolio Risk Analysis

**Account Value:** ₹${r.account_value?.toLocaleString() ?? 'N/A'}
**Positions:** ${r.positions_count ?? 'N/A'}

### Risk Assessment
${JSON.stringify(r.risk_analysis ?? {}, null, 2)}`;
    }

    // Generic response
    if (r?.response || r?.answer || r?.message) {
      return r.response || r.answer || r.message || 'No message';
    }

    // Fallback
    return typeof r === 'string' ? r : JSON.stringify(r, null, 2);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Card className={cn('flex flex-col', expanded ? 'h-[600px]' : 'h-[400px]', className)}>
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="h-5 w-5 text-purple-500" />
            Gemini AI Assistant
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              <Bot className="h-3 w-3 mr-1" />
              gemini-2.0-flash
            </Badge>
            {onToggleExpand && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onToggleExpand}>
                {expanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
        {/* Messages Area */}
        <ScrollArea className="flex-1 px-4" ref={scrollRef}>
          <div className="space-y-4 pb-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'flex gap-3',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/30">
                    <Sparkles className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  </div>
                )}
                <div
                  className={cn(
                    'rounded-lg px-4 py-2 max-w-[85%]',
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  )}
                >
                  <div className="text-sm whitespace-pre-wrap prose prose-sm dark:prose-invert max-w-none">
                    {message.content}
                  </div>
                  <p className="text-xs opacity-50 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                    <User className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/30">
                  <Loader2 className="h-4 w-4 text-purple-600 animate-spin" />
                </div>
                <div className="bg-muted rounded-lg px-4 py-3">
                  <div className="flex gap-1">
                    <div className="h-2 w-2 bg-muted-foreground/30 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="h-2 w-2 bg-muted-foreground/30 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="h-2 w-2 bg-muted-foreground/30 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Quick Actions */}
        {messages.length <= 2 && !isLoading && (
          <div className="px-4 pb-2">
            <p className="text-xs text-muted-foreground mb-2">Quick actions:</p>
            <div className="flex flex-wrap gap-1">
              {quickActions.map((action) => (
                <Button
                  key={action.label}
                  variant="outline"
                  size="sm"
                  className="text-xs h-7"
                  onClick={() => handleSend(action.query)}
                >
                  {action.label}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t">
          <div className="flex gap-2">
            <Input
              placeholder="Ask about stocks, options, market analysis..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="flex-1"
            />
            <Button onClick={() => handleSend()} disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
