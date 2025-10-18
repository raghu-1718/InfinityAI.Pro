import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Button, 
  Typography, 
  Chip,
  Grid,
  Alert,
  List,
  ListItem,
  ListItemText,
  Switch,
  FormControlLabel,
  LinearProgress
} from '@mui/material';
import { 
  PlayArrow as StartIcon,
  Stop as StopIcon,
  SmartToy as AIIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';

const AutoTrading = () => {
  const [tradingStatus, setTradingStatus] = useState('stopped');
  const [isLoading, setIsLoading] = useState(false);
  const [statusData, setStatusData] = useState(null);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const ENGINE_C_URL = process.env.REACT_APP_ENGINE_C_URL;

  // Fetch AI trading status
  const fetchTradingStatus = async () => {
    try {
      const response = await fetch(`${ENGINE_C_URL}/api/auto-trade/status`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setStatusData(data);
        setTradingStatus(data.trading_status);
        setError(null);
      } else {
        setError('Failed to fetch trading status');
      }
    } catch (err) {
      console.error('Error fetching trading status:', err);
      setError('Connection error - Engine C may be offline');
    }
  };

  // Start AI auto-trading
  const startTrading = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${ENGINE_C_URL}/api/auto-trade/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      if (data.status === 'started' || data.status === 'already_running') {
        setTradingStatus('running');
        setError(null);
        // Refresh status immediately
        setTimeout(fetchTradingStatus, 1000);
      } else {
        setError(data.message || 'Failed to start AI trading');
      }
    } catch (err) {
      console.error('Error starting trading:', err);
      setError('Failed to start AI auto-trading');
    }
    setIsLoading(false);
  };

  // Stop AI auto-trading
  const stopTrading = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${ENGINE_C_URL}/api/auto-trade/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      if (data.status === 'stopped' || data.status === 'not_running') {
        setTradingStatus('stopped');
        setError(null);
        // Refresh status immediately
        setTimeout(fetchTradingStatus, 1000);
      } else {
        setError(data.message || 'Failed to stop AI trading');
      }
    } catch (err) {
      console.error('Error stopping trading:', err);
      setError('Failed to stop AI auto-trading');
    }
    setIsLoading(false);
  };

  // Auto-refresh status
  useEffect(() => {
    fetchTradingStatus();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchTradingStatus, 5000); // Refresh every 5 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getStatusColor = () => {
    switch (tradingStatus) {
      case 'running': return 'success';
      case 'stopped': return 'error';
      default: return 'warning';
    }
  };

  const getStatusIcon = () => {
    switch (tradingStatus) {
      case 'running': return '🟢';
      case 'stopped': return '🔴';
      default: return '🟠';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AIIcon color="primary" />
        AI Auto-Execution System
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Automated trading based on AI signals for Indian markets (NSE, BSE, MCX)
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Main Control Panel */}
        <Grid item xs={12} md={6}>
          <Card elevation={3}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Trading Control</Typography>
                <Chip 
                  label={`${getStatusIcon()} ${tradingStatus.toUpperCase()}`}
                  color={getStatusColor()}
                  variant="filled"
                />
              </Box>

              <Box display="flex" gap={2} mb={3}>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<StartIcon />}
                  onClick={startTrading}
                  disabled={isLoading || tradingStatus === 'running'}
                  fullWidth
                >
                  {tradingStatus === 'running' ? 'AI Trading Active' : 'Start AI Auto Trading'}
                </Button>
                
                <Button
                  variant="contained"
                  color="error"
                  startIcon={<StopIcon />}
                  onClick={stopTrading}
                  disabled={isLoading || tradingStatus === 'stopped'}
                  fullWidth
                >
                  Stop AI Trading
                </Button>
              </Box>

              {isLoading && (
                <LinearProgress sx={{ mb: 2 }} />
              )}

              <FormControlLabel
                control={
                  <Switch
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                  />
                }
                label="Auto-refresh status"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Status Information */}
        <Grid item xs={12} md={6}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Trading Statistics</Typography>
              
              {statusData && (
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h3" color="primary">
                        {statusData.trades_executed_today}
                      </Typography>
                      <Typography variant="caption">Trades Today</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h3" color="secondary">
                        {statusData.config?.max_daily_trades || 10}
                      </Typography>
                      <Typography variant="caption">Daily Limit</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Min Confidence: {((statusData.config?.min_confidence || 0.75) * 100).toFixed(0)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Max Risk per Trade: {((statusData.config?.max_risk_per_trade || 0.02) * 100).toFixed(0)}%
                    </Typography>
                  </Grid>
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Executions */}
        <Grid item xs={12}>
          <Card elevation={3}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <TimelineIcon color="primary" />
                <Typography variant="h6">Recent AI Executions</Typography>
              </Box>
              
              {statusData?.last_execution_history?.length > 0 ? (
                <List>
                  {statusData.last_execution_history.map((trade, index) => (
                    <ListItem key={trade.order_id || index} divider>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            {trade.side === 'BUY' ? 
                              <TrendingUpIcon color="success" fontSize="small" /> : 
                              <TrendingDownIcon color="error" fontSize="small" />
                            }
                            <Typography variant="body1">
                              {trade.side} {trade.symbol}
                            </Typography>
                            <Chip 
                              label={`${trade.confidence?.toFixed(1)}%`} 
                              size="small" 
                              color={trade.confidence > 80 ? 'success' : 'warning'}
                            />
                          </Box>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary">
                            Price: ₹{trade.price?.toFixed(2)} | Qty: {trade.quantity} | {new Date(trade.timestamp).toLocaleTimeString()}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={3}>
                  No recent executions. Start AI trading to see live trades here.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AutoTrading;