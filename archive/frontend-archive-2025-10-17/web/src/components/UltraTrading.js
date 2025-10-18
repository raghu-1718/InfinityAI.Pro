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
  LinearProgress,
  Slider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  FlashOn as UltraIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  Speed as SpeedIcon,
  FlashOn
} from '@mui/icons-material';
import ApiService from '../services/ApiService';

const UltraTrading = () => {
  const [ultraStatus, setUltraStatus] = useState('disabled');
  const [isLoading, setIsLoading] = useState(false);
  const [ultraData, setUltraData] = useState(null);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [riskLevel, setRiskLevel] = useState(75);
  const [maxPosition, setMaxPosition] = useState(100000);

  const fetchUltraStatus = async () => {
    try {
      const [signalsData, tradesData] = await Promise.allSettled([
        ApiService.getUltraSignals(),
        ApiService.getAggressiveTrades()
      ]);

      const data = {
        signals: signalsData.status === 'fulfilled' ? signalsData.value : null,
        trades: tradesData.status === 'fulfilled' ? tradesData.value : null,
        timestamp: new Date().toISOString()
      };

      setUltraData(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching ultra status:', err);
      setError('Failed to connect to Engine Ultra - Service may be offline');
    }
  };

  const enableUltra = async () => {
    setIsLoading(true);
    try {
      const settings = {
        risk_level: riskLevel,
        max_position_size: maxPosition,
        market_focus: 'indian_only',
        exchanges: ['NSE', 'BSE']
      };

      await ApiService.enableUltraMode(settings);
      setUltraStatus('enabled');
      setError(null);
      setTimeout(fetchUltraStatus, 1000);
    } catch (err) {
      console.error('Error enabling ultra mode:', err);
      setError('Failed to enable Ultra Aggressive Mode');
    }
    setIsLoading(false);
  };

  const disableUltra = async () => {
    setIsLoading(true);
    try {
      await ApiService.disableUltraMode();
      setUltraStatus('disabled');
      setError(null);
      setTimeout(fetchUltraStatus, 1000);
    } catch (err) {
      console.error('Error disabling ultra mode:', err);
      setError('Failed to disable Ultra Aggressive Mode');
    }
    setIsLoading(false);
  };

  useEffect(() => {
    fetchUltraStatus();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchUltraStatus, 3000); // Faster refresh for ultra mode
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getStatusColor = () => {
    switch (ultraStatus) {
      case 'enabled': return 'error'; // Red for ultra aggressive
      case 'disabled': return 'default';
      default: return 'warning';
    }
  };

  const getStatusIcon = () => {
    switch (ultraStatus) {
      case 'enabled': return '🔥';
      case 'disabled': return '❄️';
      default: return '⚡';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <UltraIcon color="error" />
        Ultra Aggressive Trading System
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        High-frequency AI trading for maximum opportunities in Indian markets
      </Typography>

      <Alert severity="warning" sx={{ mb: 3 }}>
        <strong>⚠️ High Risk Mode:</strong> Ultra Aggressive Trading involves significant risk. 
        Only use with funds you can afford to lose.
      </Alert>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Control Panel */}
        <Grid item xs={12} md={6}>
          <Card elevation={3} sx={{ border: ultraStatus === 'enabled' ? '2px solid #f44336' : 'none' }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Ultra Control</Typography>
                <Chip 
                  label={`${getStatusIcon()} ${ultraStatus.toUpperCase()}`}
                  color={getStatusColor()}
                  variant="filled"
                />
              </Box>

              <Box display="flex" gap={2} mb={3}>
                <Button
                  variant="contained"
                  color="error"
                  startIcon={<UltraIcon />}
                  onClick={enableUltra}
                  disabled={isLoading || ultraStatus === 'enabled'}
                  fullWidth
                >
                  {ultraStatus === 'enabled' ? 'Ultra Mode Active' : 'Enable Ultra Mode'}
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<WarningIcon />}
                  onClick={disableUltra}
                  disabled={isLoading || ultraStatus === 'disabled'}
                  fullWidth
                >
                  Disable Ultra
                </Button>
              </Box>

              {isLoading && <LinearProgress sx={{ mb: 2 }} />}

              <Box display="flex" justifyContent="space-between" alignItems="center">
                <FormControlLabel
                  control={
                    <Switch
                      checked={autoRefresh}
                      onChange={(e) => setAutoRefresh(e.target.checked)}
                    />
                  }
                  label="Auto-refresh (3s)"
                />
                
                <Button 
                  variant="text" 
                  onClick={() => setSettingsOpen(true)}
                  startIcon={<SpeedIcon />}
                >
                  Settings
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Ultra Statistics */}
        <Grid item xs={12} md={6}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Ultra Performance</Typography>
              
              {ultraData?.signals && (
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h3" color="error">
                        {ultraData.signals.high_confidence_count || 0}
                      </Typography>
                      <Typography variant="caption">Ultra Signals</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h3" color="success">
                        {ultraData.signals.success_rate || '0'}%
                      </Typography>
                      <Typography variant="caption">Success Rate</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Risk Level: {riskLevel}% | Max Position: ₹{ApiService.formatINR(maxPosition)}
                    </Typography>
                  </Grid>
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Ultra Signals */}
        <Grid item xs={12}>
          <Card elevation={3}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <FlashOn color="error" />
                <Typography variant="h6">Ultra Aggressive Signals</Typography>
              </Box>
              
              {ultraData?.signals?.signals?.length > 0 ? (
                <List>
                  {ultraData.signals.signals.slice(0, 10).map((signal, index) => (
                    <ListItem key={`${signal.symbol}-${index}`} divider>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            {signal.action === 'BUY' ? 
                              <TrendingUpIcon color="success" fontSize="small" /> : 
                              <TrendingDownIcon color="error" fontSize="small" />
                            }
                            <Typography variant="body1">
                              {signal.action} {signal.symbol}
                            </Typography>
                            <Chip 
                              label={`${signal.confidence}%`} 
                              size="small" 
                              color={signal.confidence > 85 ? 'error' : 'warning'}
                            />
                            <Chip 
                              label={`₹${signal.target_price}`} 
                              size="small" 
                              variant="outlined"
                            />
                          </Box>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary">
                            Strength: {signal.signal_strength} | Risk: {signal.risk_assessment} | 
                            {new Date(signal.timestamp).toLocaleTimeString()}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={3}>
                  No ultra signals available. Enable Ultra Mode to see high-confidence opportunities.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Ultra Mode Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography gutterBottom>Risk Level: {riskLevel}%</Typography>
            <Slider
              value={riskLevel}
              onChange={(e, value) => setRiskLevel(value)}
              min={50}
              max={95}
              marks={[
                { value: 50, label: '50% (High)' },
                { value: 75, label: '75% (Ultra)' },
                { value: 95, label: '95% (Extreme)' }
              ]}
              sx={{ mb: 3 }}
            />
            
            <TextField
              fullWidth
              label="Max Position Size (₹)"
              type="number"
              value={maxPosition}
              onChange={(e) => setMaxPosition(parseInt(e.target.value) || 100000)}
              sx={{ mb: 2 }}
              helperText="Maximum amount per trade in Indian Rupees"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Cancel</Button>
          <Button onClick={() => setSettingsOpen(false)} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UltraTrading;