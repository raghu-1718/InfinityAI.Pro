import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Button
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDhanIntegration } from '../../hooks/useDhanIntegration';

const DhanCallback = () => {
  const [status, setStatus] = useState('processing'); // processing, success, error
  const [message, setMessage] = useState('Processing authorization...');
  const [error, setError] = useState(null);
  
  const location = useLocation();
  const navigate = useNavigate();
  const { handleOAuthCallback } = useDhanIntegration();

  useEffect(() => {
    const handleCallback = async () => {
      console.log('🔄 Dhan OAuth callback initiated');
      console.log('🌐 Current URL:', window.location.href);
      
      try {
        // Parse URL parameters
        const urlParams = new URLSearchParams(location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');
        const errorDescription = urlParams.get('error_description');

        console.log('📋 OAuth parameters:', {
          code: code ? `${code.substr(0, 10)}...` : null,
          state,
          error,
          errorDescription
        });

        // Check for OAuth errors
        if (error) {
          throw new Error(errorDescription || `OAuth error: ${error}`);
        }

        // Validate required parameters
        if (!code) {
          throw new Error('Authorization code not received');
        }

        if (!state) {
          throw new Error('State parameter missing');
        }

        setMessage('Validating authorization code...');

        // Process the callback through the hook
        const result = await handleOAuthCallback(code, state, state);
        
        console.log('✅ OAuth callback successful:', result);
        
        setStatus('success');
        setMessage('Successfully connected your Dhan account!');
        
        // Store successful auth in localStorage for persistence
        localStorage.setItem('dhan_auth_success', 'true');
        localStorage.setItem('dhan_auth_timestamp', new Date().toISOString());
        
        // Redirect to portfolio tab after 3 seconds
        setTimeout(() => {
          navigate('/?tab=0'); // Portfolio tab is tab 0
          // Also close this window if it was opened as popup
          if (window.opener) {
            window.close();
          }
        }, 3000);
        
      } catch (err) {
        console.error('❌ OAuth callback error:', err);
        setStatus('error');
        setError(err.message);
        setMessage('Failed to connect Dhan account');
      }
    };

    handleCallback();
  }, [location.search, handleOAuthCallback, navigate]);

  const handleRetry = () => {
    window.location.href = '/'; // Redirect to main dashboard
  };

  const handleManualRedirect = () => {
    navigate('/?tab=0'); // Go to Portfolio tab
    if (window.opener) {
      window.close();
    }
  };

  return (
    <Box 
      sx={{ 
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'grey.100',
        p: 3
      }}
    >
      <Card sx={{ maxWidth: 500, width: '100%' }}>
        <CardContent sx={{ textAlign: 'center', p: 4 }}>
          {/* Header */}
          <Typography variant="h4" sx={{ mb: 2, fontWeight: 'bold' }}>
            Dhan Integration
          </Typography>
          
          {/* Status Indicator */}
          {status === 'processing' && (
            <Box sx={{ mb: 3 }}>
              <LinearProgress sx={{ mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                {message}
              </Typography>
            </Box>
          )}
          
          {status === 'success' && (
            <Box sx={{ mb: 3 }}>
              <CheckCircle 
                sx={{ 
                  fontSize: 64, 
                  color: 'success.main',
                  mb: 2 
                }} 
              />
              <Alert severity="success" sx={{ mb: 2 }}>
                {message}
              </Alert>
              <Typography variant="body2" color="text.secondary">
                Redirecting to dashboard...
              </Typography>
            </Box>
          )}
          
          {status === 'error' && (
            <Box sx={{ mb: 3 }}>
              <ErrorIcon 
                sx={{ 
                  fontSize: 64, 
                  color: 'error.main',
                  mb: 2 
                }} 
              />
              <Alert severity="error" sx={{ mb: 2 }}>
                {message}
              </Alert>
              {error && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Error details: {error}
                </Typography>
              )}
            </Box>
          )}
          
          {/* Action Buttons */}
          {status === 'error' && (
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button 
                variant="contained" 
                onClick={handleRetry}
                color="primary"
              >
                Back to Dashboard
              </Button>
              <Button 
                variant="outlined" 
                onClick={handleManualRedirect}
              >
                Go to Broker Settings
              </Button>
            </Box>
          )}
          
          {status === 'success' && (
            <Button 
              variant="contained" 
              onClick={handleManualRedirect}
              color="success"
            >
              Continue to Dashboard
            </Button>
          )}
          
          {/* Debug Information (only in development) */}
          {process.env.NODE_ENV === 'development' && (
            <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                Debug Info:
              </Typography>
              <Typography variant="caption" sx={{ display: 'block' }} color="text.secondary">
                URL: {window.location.href}
              </Typography>
              <Typography variant="caption" sx={{ display: 'block' }} color="text.secondary">
                Status: {status}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default DhanCallback;