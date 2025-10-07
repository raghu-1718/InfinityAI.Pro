import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Alert,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Save,
  Refresh,
  Delete,
  Edit,
  Visibility,
  VisibilityOff,
  Add,
  CloudSync,
  Security,
  Notifications,
  Palette,
  AccountCircle,
  ApiSharp,
  Storage,
  Speed
} from '@mui/icons-material';

const Settings = ({ apiUrl, userId }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [settings, setSettings] = useState({
    profile: {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      timezone: 'America/New_York'
    },
    trading: {
      defaultOrderType: 'market',
      defaultTimeInForce: 'day',
      riskLimits: {
        maxPositionSize: 100000,
        maxDailyLoss: 5000,
        maxOrderValue: 50000
      },
      notifications: {
        orderFills: true,
        priceAlerts: true,
        accountUpdates: true,
        aiSignals: true
      }
    },
    brokers: [],
    apiKeys: [],
    theme: {
      mode: 'light',
      primaryColor: '#1976d2',
      fontSize: 'medium'
    },
    ai: {
      modelPreferences: {
        riskTolerance: 'moderate',
        tradingStyle: 'balanced',
        enableAutoTrading: false,
        maxAutoTradeSize: 1000
      },
      notifications: {
        aiInsights: true,
        modelUpdates: true,
        performanceAlerts: true
      }
    }
  });
  
  const [showPasswords, setShowPasswords] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [dialogOpen, setDialogOpen] = useState({ type: '', open: false, data: null });
  const [newBroker, setNewBroker] = useState({
    name: '',
    type: 'alpaca',
    apiKey: '',
    secretKey: '',
    baseUrl: '',
    sandbox: true
  });
  const [newApiKey, setNewApiKey] = useState({
    name: '',
    service: '',
    key: '',
    description: ''
  });

  const brokerTypes = [
    { value: 'alpaca', label: 'Alpaca Markets' },
    { value: 'interactive_brokers', label: 'Interactive Brokers' },
    { value: 'td_ameritrade', label: 'TD Ameritrade' },
    { value: 'robinhood', label: 'Robinhood' },
    { value: 'fidelity', label: 'Fidelity' }
  ];

  const apiServices = [
    { value: 'yahoo_finance', label: 'Yahoo Finance' },
    { value: 'alpha_vantage', label: 'Alpha Vantage' },
    { value: 'iex_cloud', label: 'IEX Cloud' },
    { value: 'finnhub', label: 'Finnhub' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic Claude' }
  ];

  const timezones = [
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Frankfurt',
    'Asia/Tokyo',
    'Asia/Hong_Kong',
    'Asia/Singapore',
    'Australia/Sydney'
  ];

useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/user/settings`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({ ...prev, ...data.settings }));
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
      setError('Failed to fetch settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async (section = null) => {
    try {
      setLoading(true);
      const payload = section ? { [section]: settings[section] } : settings;
      
      const response = await fetch(`${apiUrl}/user/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setSuccess('Settings saved successfully');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to save settings');
      }
    } catch (error) {
      setError('Error saving settings: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const addBroker = async () => {
    try {
      const response = await fetch(`${apiUrl}/user/brokers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(newBroker)
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({
          ...prev,
          brokers: [...prev.brokers, data.broker]
        }));
        setNewBroker({
          name: '',
          type: 'alpaca',
          apiKey: '',
          secretKey: '',
          baseUrl: '',
          sandbox: true
        });
        setDialogOpen({ type: '', open: false, data: null });
        setSuccess('Broker added successfully');
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to add broker');
      }
    } catch (error) {
      setError('Error adding broker: ' + error.message);
    }
  };

  const deleteBroker = async (brokerId) => {
    try {
      const response = await fetch(`${apiUrl}/user/brokers/${brokerId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        setSettings(prev => ({
          ...prev,
          brokers: prev.brokers.filter(b => b.id !== brokerId)
        }));
        setSuccess('Broker removed successfully');
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to remove broker');
      }
    } catch (error) {
      setError('Error removing broker: ' + error.message);
    }
  };

  const addApiKey = async () => {
    try {
      const response = await fetch(`${apiUrl}/user/api-keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(newApiKey)
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({
          ...prev,
          apiKeys: [...prev.apiKeys, data.apiKey]
        }));
        setNewApiKey({
          name: '',
          service: '',
          key: '',
          description: ''
        });
        setDialogOpen({ type: '', open: false, data: null });
        setSuccess('API key added successfully');
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to add API key');
      }
    } catch (error) {
      setError('Error adding API key: ' + error.message);
    }
  };

  const deleteApiKey = async (keyId) => {
    try {
      const response = await fetch(`${apiUrl}/user/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        setSettings(prev => ({
          ...prev,
          apiKeys: prev.apiKeys.filter(k => k.id !== keyId)
        }));
        setSuccess('API key removed successfully');
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to remove API key');
      }
    } catch (error) {
      setError('Error removing API key: ' + error.message);
    }
  };

  const togglePasswordVisibility = (id) => {
    setShowPasswords(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };


  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>
        Settings
      </Typography>

      {/* Alert Messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Profile" icon={<AccountCircle />} />
        <Tab label="Trading" icon={<Speed />} />
        <Tab label="Brokers" icon={<CloudSync />} />
        <Tab label="API Keys" icon={<ApiSharp />} />
        <Tab label="AI Settings" icon={<Storage />} />
        <Tab label="Appearance" icon={<Palette />} />
      </Tabs>

      {/* Profile Tab */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Profile Information
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="First Name"
                      value={settings.profile.firstName}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        profile: { ...prev.profile, firstName: e.target.value }
                      }))}
                      fullWidth
                      variant="outlined"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="Last Name"
                      value={settings.profile.lastName}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        profile: { ...prev.profile, lastName: e.target.value }
                      }))}
                      fullWidth
                      variant="outlined"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="Email"
                      type="email"
                      value={settings.profile.email}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        profile: { ...prev.profile, email: e.target.value }
                      }))}
                      fullWidth
                      variant="outlined"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="Phone"
                      value={settings.profile.phone}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        profile: { ...prev.profile, phone: e.target.value }
                      }))}
                      fullWidth
                      variant="outlined"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Timezone</InputLabel>
                      <Select
                        value={settings.profile.timezone}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          profile: { ...prev.profile, timezone: e.target.value }
                        }))}
                        label="Timezone"
                      >
                        {timezones.map((tz) => (
                          <MenuItem key={tz} value={tz}>{tz}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
                
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={() => saveSettings('profile')}
                  disabled={loading}
                  sx={{ mt: 3 }}
                >
                  Save Profile
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Trading Tab */}
      {activeTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Trading Preferences
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Default Order Type</InputLabel>
                      <Select
                        value={settings.trading.defaultOrderType}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          trading: { ...prev.trading, defaultOrderType: e.target.value }
                        }))}
                        label="Default Order Type"
                      >
                        <MenuItem value="market">Market</MenuItem>
                        <MenuItem value="limit">Limit</MenuItem>
                        <MenuItem value="stop">Stop</MenuItem>
                        <MenuItem value="stop_limit">Stop Limit</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Default Time in Force</InputLabel>
                      <Select
                        value={settings.trading.defaultTimeInForce}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          trading: { ...prev.trading, defaultTimeInForce: e.target.value }
                        }))}
                        label="Default Time in Force"
                      >
                        <MenuItem value="day">Day</MenuItem>
                        <MenuItem value="gtc">Good Till Cancelled</MenuItem>
                        <MenuItem value="ioc">Immediate or Cancel</MenuItem>
                        <MenuItem value="fok">Fill or Kill</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
                
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={() => saveSettings('trading')}
                  disabled={loading}
                  sx={{ mt: 3 }}
                >
                  Save Trading Settings
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Risk Limits
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <TextField
                      label="Max Position Size"
                      type="number"
                      value={settings.trading.riskLimits.maxPositionSize}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        trading: {
                          ...prev.trading,
                          riskLimits: {
                            ...prev.trading.riskLimits,
                            maxPositionSize: parseFloat(e.target.value)
                          }
                        }
                      }))}
                      fullWidth
                      variant="outlined"
                      InputProps={{
                        startAdornment: '$'
                      }}
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      label="Max Daily Loss"
                      type="number"
                      value={settings.trading.riskLimits.maxDailyLoss}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        trading: {
                          ...prev.trading,
                          riskLimits: {
                            ...prev.trading.riskLimits,
                            maxDailyLoss: parseFloat(e.target.value)
                          }
                        }
                      }))}
                      fullWidth
                      variant="outlined"
                      InputProps={{
                        startAdornment: '$'
                      }}
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      label="Max Order Value"
                      type="number"
                      value={settings.trading.riskLimits.maxOrderValue}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        trading: {
                          ...prev.trading,
                          riskLimits: {
                            ...prev.trading.riskLimits,
                            maxOrderValue: parseFloat(e.target.value)
                          }
                        }
                      }))}
                      fullWidth
                      variant="outlined"
                      InputProps={{
                        startAdornment: '$'
                      }}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Notification Preferences
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.trading.notifications.orderFills}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            trading: {
                              ...prev.trading,
                              notifications: {
                                ...prev.trading.notifications,
                                orderFills: e.target.checked
                              }
                            }
                          }))}
                        />
                      }
                      label="Order Fill Notifications"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.trading.notifications.priceAlerts}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            trading: {
                              ...prev.trading,
                              notifications: {
                                ...prev.trading.notifications,
                                priceAlerts: e.target.checked
                              }
                            }
                          }))}
                        />
                      }
                      label="Price Alert Notifications"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.trading.notifications.accountUpdates}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            trading: {
                              ...prev.trading,
                              notifications: {
                                ...prev.trading.notifications,
                                accountUpdates: e.target.checked
                              }
                            }
                          }))}
                        />
                      }
                      label="Account Update Notifications"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.trading.notifications.aiSignals}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            trading: {
                              ...prev.trading,
                              notifications: {
                                ...prev.trading.notifications,
                                aiSignals: e.target.checked
                              }
                            }
                          }))}
                        />
                      }
                      label="AI Signal Notifications"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Brokers Tab */}
      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6">
                    Connected Brokers
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setDialogOpen({ type: 'broker', open: true, data: null })}
                  >
                    Add Broker
                  </Button>
                </Box>
                
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Sandbox</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {settings.brokers.map((broker) => (
                        <TableRow key={broker.id}>
                          <TableCell>
                            <Typography variant="subtitle2">
                              {broker.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={broker.type} 
                              variant="outlined" 
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={broker.status || 'Connected'} 
                              color="success" 
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={broker.sandbox ? 'Yes' : 'No'} 
                              color={broker.sandbox ? 'warning' : 'default'} 
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              onClick={() => deleteBroker(broker.id)}
                              color="error"
                            >
                              <Delete />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  
                  {settings.brokers.length === 0 && (
                    <Box sx={{ p: 4, textAlign: 'center' }}>
                      <Typography color="text.secondary">
                        No brokers connected. Add a broker to start trading.
                      </Typography>
                    </Box>
                  )}
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* API Keys Tab */}
      {activeTab === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6">
                    API Keys
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setDialogOpen({ type: 'apikey', open: true, data: null })}
                  >
                    Add API Key
                  </Button>
                </Box>
                
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Service</TableCell>
                        <TableCell>Key</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {settings.apiKeys.map((apiKey) => (
                        <TableRow key={apiKey.id}>
                          <TableCell>
                            <Typography variant="subtitle2">
                              {apiKey.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={apiKey.service} 
                              variant="outlined" 
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                {showPasswords[apiKey.id] 
                                  ? apiKey.key 
                                  : apiKey.key.substring(0, 8) + '...'
                                }
                              </Typography>
                              <IconButton
                                size="small"
                                onClick={() => togglePasswordVisibility(apiKey.id)}
                                sx={{ ml: 1 }}
                              >
                                {showPasswords[apiKey.id] ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {apiKey.description}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              onClick={() => deleteApiKey(apiKey.id)}
                              color="error"
                            >
                              <Delete />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  
                  {settings.apiKeys.length === 0 && (
                    <Box sx={{ p: 4, textAlign: 'center' }}>
                      <Typography color="text.secondary">
                        No API keys configured. Add API keys for data providers and AI services.
                      </Typography>
                    </Box>
                  )}
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* AI Settings Tab */}
      {activeTab === 4 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  AI Model Preferences
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Risk Tolerance</InputLabel>
                      <Select
                        value={settings.ai.modelPreferences.riskTolerance}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          ai: {
                            ...prev.ai,
                            modelPreferences: {
                              ...prev.ai.modelPreferences,
                              riskTolerance: e.target.value
                            }
                          }
                        }))}
                        label="Risk Tolerance"
                      >
                        <MenuItem value="conservative">Conservative</MenuItem>
                        <MenuItem value="moderate">Moderate</MenuItem>
                        <MenuItem value="aggressive">Aggressive</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Trading Style</InputLabel>
                      <Select
                        value={settings.ai.modelPreferences.tradingStyle}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          ai: {
                            ...prev.ai,
                            modelPreferences: {
                              ...prev.ai.modelPreferences,
                              tradingStyle: e.target.value
                            }
                          }
                        }))}
                        label="Trading Style"
                      >
                        <MenuItem value="scalping">Scalping</MenuItem>
                        <MenuItem value="day_trading">Day Trading</MenuItem>
                        <MenuItem value="swing_trading">Swing Trading</MenuItem>
                        <MenuItem value="balanced">Balanced</MenuItem>
                        <MenuItem value="long_term">Long Term</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.ai.modelPreferences.enableAutoTrading}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            ai: {
                              ...prev.ai,
                              modelPreferences: {
                                ...prev.ai.modelPreferences,
                                enableAutoTrading: e.target.checked
                              }
                            }
                          }))}
                        />
                      }
                      label="Enable Auto Trading"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      label="Max Auto Trade Size"
                      type="number"
                      value={settings.ai.modelPreferences.maxAutoTradeSize}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        ai: {
                          ...prev.ai,
                          modelPreferences: {
                            ...prev.ai.modelPreferences,
                            maxAutoTradeSize: parseFloat(e.target.value)
                          }
                        }
                      }))}
                      fullWidth
                      variant="outlined"
                      InputProps={{
                        startAdornment: '$'
                      }}
                      disabled={!settings.ai.modelPreferences.enableAutoTrading}
                    />
                  </Grid>
                </Grid>
                
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={() => saveSettings('ai')}
                  disabled={loading}
                  sx={{ mt: 3 }}
                >
                  Save AI Settings
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  AI Notifications
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.ai.notifications.aiInsights}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            ai: {
                              ...prev.ai,
                              notifications: {
                                ...prev.ai.notifications,
                                aiInsights: e.target.checked
                              }
                            }
                          }))}
                        />
                      }
                      label="AI Insight Notifications"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.ai.notifications.modelUpdates}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            ai: {
                              ...prev.ai,
                              notifications: {
                                ...prev.ai.notifications,
                                modelUpdates: e.target.checked
                              }
                            }
                          }))}
                        />
                      }
                      label="Model Update Notifications"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.ai.notifications.performanceAlerts}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            ai: {
                              ...prev.ai,
                              notifications: {
                                ...prev.ai.notifications,
                                performanceAlerts: e.target.checked
                              }
                            }
                          }))}
                        />
                      }
                      label="Performance Alert Notifications"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Appearance Tab */}
      {activeTab === 5 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Theme Settings
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Theme Mode</InputLabel>
                      <Select
                        value={settings.theme.mode}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          theme: { ...prev.theme, mode: e.target.value }
                        }))}
                        label="Theme Mode"
                      >
                        <MenuItem value="light">Light</MenuItem>
                        <MenuItem value="dark">Dark</MenuItem>
                        <MenuItem value="auto">Auto</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      label="Primary Color"
                      type="color"
                      value={settings.theme.primaryColor}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        theme: { ...prev.theme, primaryColor: e.target.value }
                      }))}
                      fullWidth
                      variant="outlined"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Font Size</InputLabel>
                      <Select
                        value={settings.theme.fontSize}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          theme: { ...prev.theme, fontSize: e.target.value }
                        }))}
                        label="Font Size"
                      >
                        <MenuItem value="small">Small</MenuItem>
                        <MenuItem value="medium">Medium</MenuItem>
                        <MenuItem value="large">Large</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
                
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={() => saveSettings('theme')}
                  disabled={loading}
                  sx={{ mt: 3 }}
                >
                  Save Appearance
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Add Broker Dialog */}
      <Dialog open={dialogOpen.type === 'broker' && dialogOpen.open} onClose={() => setDialogOpen({ type: '', open: false, data: null })}>
        <DialogTitle>Add New Broker</DialogTitle>
        <DialogContent sx={{ minWidth: 400 }}>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Broker Name"
                value={newBroker.name}
                onChange={(e) => setNewBroker(prev => ({ ...prev, name: e.target.value }))}
                fullWidth
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Broker Type</InputLabel>
                <Select
                  value={newBroker.type}
                  onChange={(e) => setNewBroker(prev => ({ ...prev, type: e.target.value }))}
                  label="Broker Type"
                >
                  {brokerTypes.map((broker) => (
                    <MenuItem key={broker.value} value={broker.value}>
                      {broker.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="API Key"
                value={newBroker.apiKey}
                onChange={(e) => setNewBroker(prev => ({ ...prev, apiKey: e.target.value }))}
                fullWidth
                variant="outlined"
                type="password"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Secret Key"
                value={newBroker.secretKey}
                onChange={(e) => setNewBroker(prev => ({ ...prev, secretKey: e.target.value }))}
                fullWidth
                variant="outlined"
                type="password"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Base URL (Optional)"
                value={newBroker.baseUrl}
                onChange={(e) => setNewBroker(prev => ({ ...prev, baseUrl: e.target.value }))}
                fullWidth
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newBroker.sandbox}
                    onChange={(e) => setNewBroker(prev => ({ ...prev, sandbox: e.target.checked }))}
                  />
                }
                label="Use Sandbox Environment"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen({ type: '', open: false, data: null })}>
            Cancel
          </Button>
          <Button onClick={addBroker} variant="contained">
            Add Broker
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add API Key Dialog */}
      <Dialog open={dialogOpen.type === 'apikey' && dialogOpen.open} onClose={() => setDialogOpen({ type: '', open: false, data: null })}>
        <DialogTitle>Add New API Key</DialogTitle>
        <DialogContent sx={{ minWidth: 400 }}>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Key Name"
                value={newApiKey.name}
                onChange={(e) => setNewApiKey(prev => ({ ...prev, name: e.target.value }))}
                fullWidth
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Service</InputLabel>
                <Select
                  value={newApiKey.service}
                  onChange={(e) => setNewApiKey(prev => ({ ...prev, service: e.target.value }))}
                  label="Service"
                >
                  {apiServices.map((service) => (
                    <MenuItem key={service.value} value={service.value}>
                      {service.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="API Key"
                value={newApiKey.key}
                onChange={(e) => setNewApiKey(prev => ({ ...prev, key: e.target.value }))}
                fullWidth
                variant="outlined"
                type="password"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Description (Optional)"
                value={newApiKey.description}
                onChange={(e) => setNewApiKey(prev => ({ ...prev, description: e.target.value }))}
                fullWidth
                variant="outlined"
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen({ type: '', open: false, data: null })}>
            Cancel
          </Button>
          <Button onClick={addApiKey} variant="contained">
            Add API Key
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings;