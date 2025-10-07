import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  Paper,
  Box,
  Tabs,
  Tab,
  Alert,
  Chip
} from '@mui/material';
import {
  TrendingUp,
  AccountBalance,
  Notifications,
  Dashboard as DashboardIcon
} from '@mui/icons-material';

import Portfolio from './components/Portfolio';
import Trading from './components/Trading';
import MarketAnalysis from './components/MarketAnalysis';
import AIInsights from './components/AIInsights';
import ChatBot from './components/ChatBot';
import SettingsComponent from './components/Settings';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8003';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [currentTab, setCurrentTab] = useState(0);
const [user] = useState({ id: 'demo-user', name: 'Demo User' });
  const [systemStatus, setSystemStatus] = useState('loading');
  const [notifications, setNotifications] = useState([]);
const [marketData] = useState({});

  useEffect(() => {
    // Check system status on load
    checkSystemStatus();
    
    // Set up periodic status checks
    const statusInterval = setInterval(checkSystemStatus, 30000);
    
    return () => clearInterval(statusInterval);
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/status`);
      const data = await response.json();
      setSystemStatus('healthy');
      
      // Check individual engine health
      const engines = ['engine_a', 'engine_b', 'engine_c', 'engine_d'];
      const healthyEngines = engines.filter(engine => 
        data.engines && data.engines[engine] && data.engines[engine].status === 'healthy'
      ).length;
      
      if (healthyEngines < engines.length) {
        setNotifications(prev => [...prev, {
          id: Date.now(),
          type: 'warning',
          message: `${healthyEngines}/${engines.length} engines healthy`
        }]);
      }
    } catch (error) {
      setSystemStatus('error');
      setNotifications(prev => [...prev, {
        id: Date.now(),
        type: 'error',
        message: 'System health check failed'
      }]);
    }
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'loading': return 'info';
      case 'error': return 'error';
      default: return 'warning';
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ 
        background: 'linear-gradient(45deg, #1976d2 30%, #21CBF3 90%)',
        boxShadow: '0 3px 5px 2px rgba(25, 118, 210, .3)'
      }}>
        <Toolbar>
          <DashboardIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            InfinityAI.Pro - AI Trading Platform
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              icon={<Notifications />} 
              label={notifications.length} 
              color="secondary" 
              size="small"
            />
            <Chip 
              label={systemStatus} 
              color={getStatusColor(systemStatus)}
              size="small"
            />
            <Typography variant="body2">
              Welcome, {user.name}
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
        {/* Notifications */}
        {notifications.slice(-3).map((notification) => (
          <Alert 
            key={notification.id}
            severity={notification.type}
            sx={{ mb: 1 }}
            onClose={() => setNotifications(prev => 
              prev.filter(n => n.id !== notification.id)
            )}
          >
            {notification.message}
          </Alert>
        ))}

        {/* Quick Stats */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <AccountBalance color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Portfolio Value
                    </Typography>
                    <Typography variant="h6">
                      $125,430.50
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TrendingUp color="success" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Today's P&L
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      +$2,340.75 (1.9%)
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <SmartToy color="secondary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      AI Signals Today
                    </Typography>
                    <Typography variant="h6">
                      23 signals
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Timeline color="info" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Active Trades
                    </Typography>
                    <Typography variant="h6">
                      8 positions
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Main Navigation Tabs */}
        <Paper sx={{ width: '100%' }}>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab icon={<DashboardIcon />} label="Portfolio" />
            <Tab icon={<TrendingUp />} label="Trading" />
            <Tab icon={<Timeline />} label="Analysis" />
            <Tab icon={<SmartToy />} label="AI Insights" />
            <Tab icon={<Chat />} label="Chat Assistant" />
            <Tab icon={<SettingsIcon />} label="Settings" />
          </Tabs>

          <TabPanel value={currentTab} index={0}>
            <Portfolio userId={user.id} apiUrl={API_BASE_URL} />
          </TabPanel>

          <TabPanel value={currentTab} index={1}>
            <Trading userId={user.id} apiUrl={API_BASE_URL} />
          </TabPanel>

          <TabPanel value={currentTab} index={2}>
            <MarketAnalysis apiUrl={API_BASE_URL} />
          </TabPanel>

          <TabPanel value={currentTab} index={3}>
            <AIInsights apiUrl={API_BASE_URL} userId={user.id} />
          </TabPanel>

          <TabPanel value={currentTab} index={4}>
            <ChatBot userId={user.id} apiUrl={API_BASE_URL} />
          </TabPanel>

          <TabPanel value={currentTab} index={5}>
            <SettingsComponent userId={user.id} apiUrl={API_BASE_URL} />
          </TabPanel>
        </Paper>
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          backgroundColor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider'
        }}
      >
        <Container maxWidth="xl">
          <Typography variant="body2" color="text.secondary" align="center">
            © 2025 InfinityAI.Pro - AI-Powered Multi-Cloud Trading Platform
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}

export default App;