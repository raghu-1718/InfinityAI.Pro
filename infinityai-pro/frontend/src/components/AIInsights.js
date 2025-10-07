import React, { useState, useEffect, useCallback } from 'react';
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
  Avatar
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

const AIInsights = ({ apiUrl, userId }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [insights, setInsights] = useState([]);
  const [modelStatus, setModelStatus] = useState({});
  const [performance, setPerformance] = useState({});
  const [predictions, setPredictions] = useState([]);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ws, setWs] = useState(null);

useEffect(() => {
    fetchAIInsights();
    fetchModelStatus();
    fetchPerformanceMetrics();
    fetchPredictions();
    connectWebSocket();
  }, [connectWebSocket, fetchAIInsights, fetchModelStatus, fetchPerformanceMetrics, fetchPredictions]);

  // Connect to WebSocket for real-time AI updates
  const connectWebSocket = useCallback(() => {
    const wsUrl = `ws://localhost:8002/ws/ai/${userId}`;
    
    try {
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('AI WebSocket connected');
        setWs(websocket);
      };
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'ai_insight') {
          setInsights(prev => [data.insight, ...prev.slice(0, 19)]);
        } else if (data.type === 'model_update') {
          setModelStatus(prev => ({
            ...prev,
            [data.model]: data.status
          }));
        } else if (data.type === 'ai_signal') {
          setSignals(prev => [data.signal, ...prev.slice(0, 9)]);
        } else if (data.type === 'performance_update') {
          setPerformance(prev => ({
            ...prev,
            ...data.performance
          }));
        }
      };
      
      websocket.onerror = (error) => {
        console.error('AI WebSocket error:', error);
      };
      
      websocket.onclose = () => {
        console.log('AI WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      return websocket;
    } catch (error) {
      console.error('Failed to connect to AI WebSocket:', error);
    }
  }, [userId]);

  const fetchAIInsights = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl.replace('8003', '8002')}/insights`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setInsights(data.insights || []);
      }
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      setError('Failed to fetch AI insights');
    } finally {
      setLoading(false);
    }
  };

  const fetchModelStatus = async () => {
    try {
      const response = await fetch(`${apiUrl.replace('8003', '8002')}/models/status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setModelStatus(data.models || {});
      }
    } catch (error) {
      console.error('Error fetching model status:', error);
    }
  };

  const fetchPerformanceMetrics = async () => {
    try {
      const response = await fetch(`${apiUrl.replace('8003', '8002')}/performance`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPerformance(data.performance || {});
      }
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
    }
  };

  const fetchPredictions = async () => {
    try {
      const response = await fetch(`${apiUrl.replace('8003', '8002')}/predictions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPredictions(data.predictions || []);
        setSignals(data.signals || []);
      }
    } catch (error) {
      console.error('Error fetching predictions:', error);
    }
  };

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

  const refreshAllData = () => {
    fetchAIInsights();
    fetchModelStatus();
    fetchPerformanceMetrics();
    fetchPredictions();
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          AI Insights & Analytics
        </Typography>
        <Box>
          <Tooltip title="Refresh Data">
            <IconButton onClick={refreshAllData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
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

      {/* Model Status Tab */}
      {activeTab === 1 && (
        <Grid container spacing={3}>
          {/* Model Status Cards */}
          <Grid item xs={12}>
            <Grid container spacing={3}>
              {Object.entries(modelStatus).map(([modelName, status]) => (
                <Grid item xs={12} md={6} lg={4} key={modelName}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Memory sx={{ mr: 1, color: getStatusColor(status.status) + '.main' }} />
                        <Typography variant="h6">
                          {modelName}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Chip 
                          label={status.status || 'Unknown'} 
                          color={getStatusColor(status.status)} 
                          size="small"
                        />
                      </Box>
                      
                      {status.accuracy && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" color="text.secondary">
                            Accuracy: {formatPercentage(status.accuracy)}
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={status.accuracy * 100} 
                            sx={{ mt: 1 }}
                          />
                        </Box>
                      )}
                      
                      {status.last_training && (
                        <Typography variant="caption" color="text.secondary">
                          Last trained: {new Date(status.last_training).toLocaleString()}
                        </Typography>
                      )}
                      
                      {status.gpu_usage && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2" color="text.secondary">
                            GPU Usage: {status.gpu_usage}%
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={status.gpu_usage} 
                            color="warning"
                            sx={{ mt: 1 }}
                          />
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>
          
          {Object.keys(modelStatus).length === 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ p: 4, textAlign: 'center' }}>
                    <Memory sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography color="text.secondary">
                      No model status information available
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* Performance Tab */}
      {activeTab === 2 && (
        <Grid container spacing={3}>
          {/* Performance Metrics */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Model Performance Metrics
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Overall Accuracy:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {formatPercentage(performance.accuracy || 0)}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(performance.accuracy || 0) * 100} 
                      color="success"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Precision:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {formatPercentage(performance.precision || 0)}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(performance.precision || 0) * 100} 
                      color="info"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Recall:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {formatPercentage(performance.recall || 0)}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(performance.recall || 0) * 100} 
                      color="warning"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="body2" color="text.secondary">
                      Total Predictions: {performance.total_predictions?.toLocaleString() || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Successful Trades: {performance.successful_trades?.toLocaleString() || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Win Rate: {formatPercentage(performance.win_rate || 0)}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Performance Chart */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Performance Trend
                </Typography>
                
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performance.history || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line 
                      type="monotone" 
                      dataKey="accuracy" 
                      stroke="#8884d8" 
                      strokeWidth={2}
                      name="Accuracy"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="win_rate" 
                      stroke="#82ca9d" 
                      strokeWidth={2}
                      name="Win Rate"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          
          {/* ROI Analysis */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  AI Trading ROI Analysis
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main">
                        {formatCurrency(performance.total_profit || 0)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Profit
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="info.main">
                        {formatPercentage(performance.roi || 0)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        ROI
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="warning.main">
                        {performance.sharpe_ratio?.toFixed(2) || '0.00'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Sharpe Ratio
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="error.main">
                        {formatPercentage(performance.max_drawdown || 0)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Max Drawdown
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Predictions Tab */}
      {activeTab === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  AI Market Predictions
                </Typography>
                
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell>Prediction</TableCell>
                        <TableCell align="right">Target Price</TableCell>
                        <TableCell align="right">Current Price</TableCell>
                        <TableCell align="right">Potential Return</TableCell>
                        <TableCell align="right">Confidence</TableCell>
                        <TableCell>Time Horizon</TableCell>
                        <TableCell>Created</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {predictions.map((prediction, index) => (
                        <TableRow key={index} hover>
                          <TableCell>
                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                              {prediction.symbol}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={prediction.direction} 
                              color={getSignalColor(prediction.direction)} 
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">
                            {formatCurrency(prediction.target_price)}
                          </TableCell>
                          <TableCell align="right">
                            {formatCurrency(prediction.current_price)}
                          </TableCell>
                          <TableCell align="right">
                            <Typography 
                              sx={{ 
                                color: getConfidenceColor(prediction.potential_return * 100),
                                fontWeight: 'bold'
                              }}
                            >
                              {formatPercentage(prediction.potential_return)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Typography variant="body2" sx={{ mr: 1 }}>
                                {prediction.confidence}%
                              </Typography>
                              <LinearProgress 
                                variant="determinate" 
                                value={prediction.confidence} 
                                sx={{ width: 60, height: 6 }}
                              />
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={prediction.time_horizon} 
                              size="small" 
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {new Date(prediction.created_at).toLocaleDateString()}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                
                {predictions.length === 0 && (
                  <Box sx={{ p: 4, textAlign: 'center' }}>
                    <Timeline sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography color="text.secondary">
                      No predictions available. AI models are analyzing market data.
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default AIInsights;