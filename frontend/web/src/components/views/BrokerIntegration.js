import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Button,
  Chip,
  Alert,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Paper
} from '@mui/material';
import {
  AccountBalance,
  CheckCircle,
  Error,
  Refresh,
  Link as LinkIcon,
  LinkOff,
  Security,
  Info,
  Close as CloseIcon,
  Launch,
  AccountBalanceWallet,
  TrendingUp,
  History
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useDhanIntegration } from '../../hooks/useDhanIntegration';

const BrokerIntegration = ({ userId, apiUrl }) => {
  console.log('🏦 BrokerIntegration component mounted with userId:', userId);

  const [confirmDisconnect, setConfirmDisconnect] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [lastAction, setLastAction] = useState(null);

  // Use Dhan integration hook
  const {
    connectionStatus,
    authFlow,
    initiateOAuth,
    disconnectAccount,
    checkConnectionStatus,
    urls
  } = useDhanIntegration();

  // Component lifecycle logging
  useEffect(() => {
    console.log('📊 BrokerIntegration component mounted');
    return () => console.log('📊 BrokerIntegration component unmounted');
  }, []);

  // Log connection status changes
  useEffect(() => {
    console.log('🔄 Connection status update:', connectionStatus);
  }, [connectionStatus]);

  const handleConnectClick = async () => {
    try {
      setLastAction('connecting');
      console.log('🔗 User initiated Dhan connection');
      await initiateOAuth();
      setLastAction('oauth_opened');
    } catch (error) {
      console.error('❌ Failed to initiate OAuth:', error);
      setLastAction('error');
    }
  };

  const handleDisconnectClick = async () => {
    try {
      setLastAction('disconnecting');
      console.log('🔌 User initiated Dhan disconnection');
      await disconnectAccount();
      setConfirmDisconnect(false);
      setLastAction('disconnected');
    } catch (error) {
      console.error('❌ Failed to disconnect:', error);
      setLastAction('error');
    }
  };

  const handleRefreshStatus = async () => {
    try {
      setLastAction('refreshing');
      console.log('🔄 Refreshing connection status');
      await checkConnectionStatus();
      setLastAction('refreshed');
    } catch (error) {
      console.error('❌ Failed to refresh status:', error);
      setLastAction('error');
    }
  };

  const getStatusColor = (isConnected) => {
    return isConnected ? 'success' : 'error';
  };

  const getStatusIcon = (isConnected) => {
    return isConnected ? <CheckCircle /> : <Error />;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    return format(new Date(timestamp), 'MMM dd, yyyy HH:mm:ss');
  };

  if (connectionStatus.loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>
          Checking broker connection status...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Broker Integration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Connect your trading accounts for seamless execution
          </Typography>
        </Box>
        <Box>
          <Tooltip title="Refresh Status">
            <IconButton 
              onClick={handleRefreshStatus} 
              disabled={connectionStatus.loading || authFlow.isInitiating}
            >
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Connection Status Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <AccountBalance />
                </Avatar>
                <Box>
                  <Typography variant="h6">Dhan Trading Account</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Connect your Dhan demat account for live trading
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Chip
                  icon={getStatusIcon(connectionStatus.isConnected)}
                  label={connectionStatus.isConnected ? 'Connected' : 'Not Connected'}
                  color={getStatusColor(connectionStatus.isConnected)}
                  variant="filled"
                />
                {!connectionStatus.isConnected ? (
                  <Button
                    variant="contained"
                    startIcon={<LinkIcon />}
                    onClick={handleConnectClick}
                    disabled={authFlow.isInitiating}
                    sx={{ ml: 2 }}
                  >
                    {authFlow.isInitiating ? 'Connecting...' : 'Connect Dhan'}
                  </Button>
                ) : (
                  <Button
                    variant="outlined"
                    startIcon={<LinkOff />}
                    onClick={() => setConfirmDisconnect(true)}
                    color="error"
                    sx={{ ml: 2 }}
                  >
                    Disconnect
                  </Button>
                )}
              </Box>

              {connectionStatus.lastUpdated && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Last checked: {formatTimestamp(connectionStatus.lastUpdated)}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                  <Security />
                </Avatar>
                <Box>
                  <Typography variant="h6">Security & Compliance</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Your credentials are stored securely
                  </Typography>
                </Box>
              </Box>

              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircle color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="OAuth 2.0 Authentication"
                    secondary="Industry-standard secure authentication"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircle color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Encrypted Token Storage"
                    secondary="Tokens encrypted at rest and in transit"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircle color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Regular Validation"
                    secondary="Automatic token refresh and validation"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Account Details (if connected) */}
      {connectionStatus.isConnected && connectionStatus.accountDetails && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Account Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <AccountBalanceWallet sx={{ mr: 1, color: 'primary.main' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">Account ID</Typography>
                    <Typography variant="body1">{connectionStatus.accountDetails.account_id || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">Account Type</Typography>
                    <Typography variant="body1">{connectionStatus.accountDetails.account_type || 'Trading'}</Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <History sx={{ mr: 1, color: 'info.main' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">Connected Since</Typography>
                    <Typography variant="body1">
                      {formatTimestamp(connectionStatus.accountDetails.connected_at)}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Connection Instructions */}
      {!connectionStatus.isConnected && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              How to Connect Your Dhan Account
            </Typography>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                You can also initiate the connection process through our AI chatbot by saying: 
                <strong> "Connect my Dhan account"</strong>
              </Typography>
            </Alert>

            <List>
              <ListItem>
                <ListItemIcon>
                  <Typography variant="h6" color="primary">1</Typography>
                </ListItemIcon>
                <ListItemText
                  primary="Click 'Connect Dhan' button"
                  secondary="This will open Dhan's secure authentication page in a new window"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Typography variant="h6" color="primary">2</Typography>
                </ListItemIcon>
                <ListItemText
                  primary="Login to your Dhan account"
                  secondary="Use your existing Dhan credentials to authenticate"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Typography variant="h6" color="primary">3</Typography>
                </ListItemIcon>
                <ListItemText
                  primary="Authorize InfinityAI.Pro"
                  secondary="Grant permissions for trading, portfolio access, and market data"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Typography variant="h6" color="primary">4</Typography>
                </ListItemIcon>
                <ListItemText
                  primary="Automatic redirect"
                  secondary="You'll be redirected back to the dashboard with your account connected"
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      )}

      {/* OAuth URLs (for debugging/chatbot reference) */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Integration Details</Typography>
            <Button
              startIcon={<Info />}
              onClick={() => setShowDetails(!showDetails)}
              variant="text"
              size="small"
            >
              {showDetails ? 'Hide' : 'Show'} Details
            </Button>
          </Box>
          
          {showDetails && (
            <Box>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>OAuth Configuration:</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Redirect URI:</strong> {urls.redirectUri}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Postback URL:</strong> {urls.postbackUrl}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Engine C Backend:</strong> {urls.engineC}
                </Typography>
              </Paper>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Last Action Status */}
      {lastAction && (
        <Alert 
          severity={lastAction === 'error' ? 'error' : 'success'} 
          sx={{ mt: 2 }}
          onClose={() => setLastAction(null)}
        >
          {lastAction === 'connecting' && 'Initiating OAuth flow...'}
          {lastAction === 'oauth_opened' && 'OAuth window opened. Please complete authentication in the new window.'}
          {lastAction === 'disconnecting' && 'Disconnecting account...'}
          {lastAction === 'disconnected' && 'Account disconnected successfully!'}
          {lastAction === 'refreshing' && 'Refreshing status...'}
          {lastAction === 'refreshed' && 'Status refreshed successfully!'}
          {lastAction === 'error' && 'An error occurred. Please try again.'}
        </Alert>
      )}

      {/* Disconnect Confirmation Dialog */}
      <Dialog
        open={confirmDisconnect}
        onClose={() => setConfirmDisconnect(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Disconnect Dhan Account</Typography>
            <IconButton onClick={() => setConfirmDisconnect(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will disconnect your Dhan account and revoke all trading permissions.
          </Alert>
          <Typography>
            Are you sure you want to disconnect your Dhan account? You'll need to re-authenticate 
            to restore trading functionality.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDisconnect(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleDisconnectClick}
            color="error"
            variant="contained"
            startIcon={<LinkOff />}
          >
            Disconnect
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BrokerIntegration;