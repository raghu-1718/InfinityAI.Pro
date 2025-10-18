import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useSearchParams } from 'react-router-dom';
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
  Chip,
  CircularProgress
} from '@mui/material';
import {
  TrendingUp,
  AccountBalance,
  Notifications,
  Dashboard as DashboardIcon,
  SmartToy,
  Timeline,
  Chat,
  Link as LinkIcon,
  Settings as SettingsIcon,
  Refresh,
  PlayArrow as AutoTradeIcon,
  FlashOn as UltraIcon
} from '@mui/icons-material';

import Portfolio from './components/views/Portfolio';
import Trading from './components/views/Trading';
import MarketAnalysis from './components/views/MarketAnalysis';
import AIInsights from './components/views/AIInsights';
import ChatBot from './components/views/ChatBot';
import BrokerIntegration from './components/views/BrokerIntegration';
import SettingsComponent from './components/views/Settings';
import AutoTrading from './components/AutoTrading';
import UltraTrading from './components/UltraTrading';
import AIChatbot from './components/AIChatbot';
import DhanCallback from './components/auth/DhanCallback';
import { useSystemHealth, usePortfolioData, useAIInsights } from './hooks/useEngineData';
import ApiService from './services/ApiService';

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

function Dashboard() {
  const [searchParams] = useSearchParams();
  const [currentTab, setCurrentTab] = useState(parseInt(searchParams.get('tab')) || 0);
  const [user, setUser] = useState({ id: 'demo-user', name: 'Demo User' });
  const [notifications, setNotifications] = useState([]);
  
  // Use real-time hooks for live data
  const { overallHealth, healthStatus, healthyCount, totalCount, loading: healthLoading } = useSystemHealth(30000);
  const portfolioData = usePortfolioData();
  const { data: aiData, loading: aiLoading } = useAIInsights(15000);
  
  // Component lifecycle logging
  useEffect(() => {
    console.log('🖥️ App component mounted');
    console.log('🔍 Environment variables check:', {
      ENGINE_A: process.env.REACT_APP_ENGINE_A_URL,
      ENGINE_B: process.env.REACT_APP_ENGINE_B_URL,
      ENGINE_C: process.env.REACT_APP_ENGINE_C_URL,
      ENGINE_D: process.env.REACT_APP_ENGINE_D_URL,
      ENGINE_ULTRA: process.env.REACT_APP_ENGINE_ULTRA_URL
    });
    return () => console.log('🖥️ App component unmounting');
  }, []);
  
  // Log data updates and update user info
  useEffect(() => {
    console.log('📈 App - Portfolio data update:', {
      totalValue: portfolioData.totalValue,
      loading: portfolioData.loading,
      error: portfolioData.error,
      lastUpdated: portfolioData.lastUpdated
    });
    
    // Update user name from portfolio data if available
    if (portfolioData.user && portfolioData.user.name && portfolioData.user.name !== 'Demo User') {
      setUser(prev => ({ ...prev, name: portfolioData.user.name }));
    }
  }, [portfolioData]);
  
  useEffect(() => {
    console.log('🤖 App - AI data update:', {
      data: aiData,
      loading: aiLoading,
      timestamp: new Date().toISOString()
    });
  }, [aiData, aiLoading]);

  useEffect(() => {
    // Monitor system health changes and create notifications
    if (healthStatus && Object.keys(healthStatus).length > 0) {
      const offlineEngines = Object.entries(healthStatus)
        .filter(([_, status]) => status.status !== 'healthy')
        .map(([engine, _]) => engine);
      
      if (offlineEngines.length > 0) {
        setNotifications(prev => [
          ...prev.slice(-4), // Keep only recent notifications
          {
            id: Date.now(),
            type: 'warning',
            message: `${healthyCount}/${totalCount} engines healthy - ${offlineEngines.join(', ')} offline`
          }
        ]);
      }
    }
  }, [healthStatus, healthyCount, totalCount]);


  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
    // Update URL without page reload
    const newSearchParams = new URLSearchParams(searchParams);
    newSearchParams.set('tab', newValue);
    window.history.replaceState({}, '', `${window.location.pathname}?${newSearchParams}`);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'partial': return 'warning'; 
      case 'error': return 'error';
      default: return 'info';
    }
  };
  
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(value);
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
              label={healthLoading ? 'checking...' : overallHealth} 
              color={getStatusColor(overallHealth)}
              size="small"
            />
            {healthLoading && (
              <CircularProgress size={16} sx={{ ml: 1 }} />
            )}
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
                      {portfolioData.loading ? (
                        <CircularProgress size={20} />
                      ) : (
                        formatCurrency(portfolioData.totalValue)
                      )}
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
                    <Typography variant="h6" color={portfolioData.todaysPnL >= 0 ? 'success.main' : 'error.main'}>
                      {portfolioData.loading ? (
                        <CircularProgress size={20} />
                      ) : (
                        `${portfolioData.todaysPnL >= 0 ? '+' : ''}${formatCurrency(portfolioData.todaysPnL)} (${portfolioData.todaysPnLPercent >= 0 ? '+' : ''}${portfolioData.todaysPnLPercent}%)`
                      )}
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
                      {aiLoading ? (
                        <CircularProgress size={20} />
                      ) : (
                        `${aiData?.signals?.length || 0} signals`
                      )}
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
                      {portfolioData.loading ? (
                        <CircularProgress size={20} />
                      ) : (
                        `${portfolioData.activePositions} positions`
                      )}
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
            <Tab icon={<AutoTradeIcon />} label="AI Auto-Trading" />
            <Tab icon={<UltraIcon />} label="Ultra Mode" />
            <Tab icon={<Timeline />} label="Analysis" />
            <Tab icon={<SmartToy />} label="AI Insights" />
            <Tab icon={<Chat />} label="AI Assistant" />
            <Tab icon={<LinkIcon />} label="Broker Integration" />
            <Tab icon={<SettingsIcon />} label="Settings" />
          </Tabs>

          <TabPanel value={currentTab} index={0}>
            <Portfolio userId={user.id} apiUrl={API_BASE_URL} />
          </TabPanel>

          <TabPanel value={currentTab} index={1}>
            <Trading userId={user.id} apiUrl={API_BASE_URL} />
          </TabPanel>

          <TabPanel value={currentTab} index={2}>
            <AutoTrading />
          </TabPanel>

          <TabPanel value={currentTab} index={3}>
            <UltraTrading />
          </TabPanel>

          <TabPanel value={currentTab} index={4}>
            <MarketAnalysis apiUrl={API_BASE_URL} />
          </TabPanel>

          <TabPanel value={currentTab} index={5}>
            <AIInsights apiUrl={API_BASE_URL} userId={user.id} />
          </TabPanel>

          <TabPanel value={currentTab} index={6}>
            <AIChatbot />
          </TabPanel>

          <TabPanel value={currentTab} index={7}>
            <BrokerIntegration userId={user.id} apiUrl={API_BASE_URL} />
          </TabPanel>

          <TabPanel value={currentTab} index={8}>
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

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/auth/dhan/callback" element={<DhanCallback />} />
      </Routes>
    </Router>
  );
}

export default App;
