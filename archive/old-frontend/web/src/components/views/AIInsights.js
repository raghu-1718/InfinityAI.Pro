import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  List,
  ListItem,
  Divider,
  Avatar,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  TrendingUp,
  Psychology,
  Analytics,
  Refresh,
  Warning,
  Info,
  SmartToy,
  Memory,
  Timeline,
  Assessment
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer
} from 'recharts';
import { useAIInsights, useWebSocket } from '../../hooks/useEngineData';

const AIInsights = ({ apiUrl, userId }) => {
  const [activeTab, setActiveTab] = useState(0);
  
  // Use real-time AI insights hook
  const { data: aiData, loading, error, lastUpdated, refetch } = useAIInsights(15000);
  
  // WebSocket for real-time AI updates
  const { messages: aiMessages, isConnected } = useWebSocket('B', '/ws/ai');
  
  // Parse AI data with fallback to sample data
  const insights = aiData?.insights || [
    {
      type: 'recommendation',
      title: 'TSLA Long Position Recommended',
      message: 'Technical indicators suggest strong upward momentum. RSI oversold, MACD bullish crossover.',
      confidence: 87,
      symbol: 'TSLA',
      timestamp: new Date().toISOString()
    },
    {
      type: 'warning',
      title: 'Market Volatility Alert',
      message: 'Increased volatility detected in tech sector. Consider risk management.',
      confidence: 94,
      symbol: 'QQQ',
      timestamp: new Date(Date.now() - 300000).toISOString()
    }
  ];
  
  const modelStatus = aiData?.models || {
    'LSTM Predictor': { status: 'running', accuracy: 0.78, last_training: new Date().toISOString(), gpu_usage: 65 },
    'CNN Analyzer': { status: 'training', accuracy: 0.82, last_training: new Date().toISOString(), gpu_usage: 85 },
    'Transformer Model': { status: 'healthy', accuracy: 0.91, last_training: new Date().toISOString(), gpu_usage: 45 }
  };
  
  const performance = aiData?.performance || {
    accuracy: 0.85,
    precision: 0.78,
    recall: 0.82,
    total_predictions: 1247,
    successful_trades: 1098,
    win_rate: 0.88,
    total_profit: 45830.50,
    roi: 0.234,
    sharpe_ratio: 1.85,
    max_drawdown: 0.087,
    history: [
      { date: '2024-01-01', accuracy: 0.82, win_rate: 0.85 },
      { date: '2024-01-02', accuracy: 0.84, win_rate: 0.87 },
      { date: '2024-01-03', accuracy: 0.85, win_rate: 0.88 }
    ]
  };
  
  const predictions = aiData?.predictions || [
    {
      symbol: 'AAPL',
      direction: 'buy',
      target_price: 195.50,
      current_price: 185.20,
      potential_return: 0.056,
      confidence: 89,
      time_horizon: '1-2 weeks',
      created_at: new Date().toISOString()
    },
    {
      symbol: 'NVDA',
      direction: 'strong_buy',
      target_price: 485.00,
      current_price: 445.30,
      potential_return: 0.089,
      confidence: 92,
      time_horizon: '2-4 weeks',
      created_at: new Date().toISOString()
    }
  ];
  
  const signals = aiData?.signals || [
    {
      symbol: 'SPY',
      signal: 'buy',
      target_price: 425.50,
      timestamp: new Date().toISOString()
    },
    {
      symbol: 'META',
      signal: 'hold',
      target_price: 315.20,
      timestamp: new Date().toISOString()
    }
  ];

  const refreshAllData = useCallback(() => {
    refetch();
  }, [refetch]);

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'running':
      case 'active': return 'success';
      case 'training':
      case 'updating': return 'warning';
      case 'error':
      case 'failed': return 'error';
      case 'idle':
      case 'stopped': return 'default';
      default: return 'info';
    }
  };

  const getSignalColor = (signal) => {
    switch (signal?.toLowerCase()) {
      case 'strong_buy':
      case 'buy': return 'success';
      case 'strong_sell':
      case 'sell': return 'error';
      case 'hold': return 'warning';
      default: return 'default';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'success.main';
    if (confidence >= 60) return 'warning.main';
    return 'error.main';
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          AI Insights & Analytics
          <Chip 
            label={isConnected ? 'Live' : 'Offline'} 
            color={isConnected ? 'success' : 'error'} 
            size="small" 
            sx={{ ml: 2 }}
          />
        </Typography>
        <Box>
          <Typography variant="caption" sx={{ mr: 2 }}>
            Last updated: {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Never'}
          </Typography>
          <Tooltip title="Refresh Data">
            <IconButton onClick={refreshAllData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="AI Insights" icon={<Psychology />} />
        <Tab label="Model Status" icon={<Memory />} />
        <Tab label="Performance" icon={<Analytics />} />
        <Tab label="Predictions" icon={<Timeline />} />
      </Tabs>

      {/* AI Insights Tab */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          {/* Latest AI Insights */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Latest AI Insights
                </Typography>
                
                <List>
                  {insights.slice(0, 10).map((insight, index) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemIcon>
                          <Avatar sx={{ bgcolor: getStatusColor(insight.type) + '.main' }}>
                            {insight.type === 'recommendation' ? <TrendingUp /> :
                             insight.type === 'warning' ? <Warning /> :
                             insight.type === 'analysis' ? <Assessment /> : <Info />}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle2">
                                {insight.title}
                              </Typography>
                              <Chip 
                                label={insight.type} 
                                size="small" 
                                color={getStatusColor(insight.type)}
                              />
                              {insight.confidence && (
                                <Chip 
                                  label={`${insight.confidence}% confidence`}
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                {insight.message}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {new Date(insight.timestamp).toLocaleString()}
                                {insight.symbol && ` • ${insight.symbol}`}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < insights.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
                
                {insights.length === 0 && (
                  <Box sx={{ p: 4, textAlign: 'center' }}>
                    <SmartToy sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography color="text.secondary">
                      No AI insights available yet. The AI models are learning from market data.
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
          
          {/* Recent AI Signals */}
          <Grid item xs={12} lg={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Recent AI Signals
                </Typography>
                
                <List dense>
                  {signals.slice(0, 5).map((signal, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Typography variant="subtitle2">
                              {signal.symbol}
                            </Typography>
                            <Chip 
                              label={signal.signal} 
                              size="small" 
                              color={getSignalColor(signal.signal)}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                              Target: {formatCurrency(signal.target_price)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(signal.timestamp).toLocaleTimeString()}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
                
                {signals.length === 0 && (
                  <Box sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      No recent signals
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Other tabs content would go here */}
    </Box>
  );
};

export default AIInsights;