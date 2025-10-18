import { useState, useEffect, useCallback } from 'react';

// Dhan Integration Hook for OAuth flow and connection management
export const useDhanIntegration = () => {
  const [connectionStatus, setConnectionStatus] = useState({
    isConnected: false,
    loading: true,
    error: null,
    accountDetails: null,
    lastUpdated: null
  });

  const [authFlow, setAuthFlow] = useState({
    isInitiating: false,
    authUrl: null,
    state: null,
    error: null
  });

  // ✅ Frontend and Backend URLs - FINAL PRODUCTION
  const FRONTEND_URL = 'https://infinityai.pro';
  const ENGINE_C_URL = process.env.REACT_APP_ENGINE_C_URL || 'https://infinityai.pro/api/engine-c';
  
  // Dhan OAuth Configuration
  const [dhanConfig, setDhanConfig] = useState({
    client_id: process.env.REACT_APP_DHAN_CLIENT_ID || 'demo_client_id',
    redirect_uri: `${FRONTEND_URL}/auth/dhan/callback`,
    postback_url: `${FRONTEND_URL}/api/webhooks/dhan`,
    scope: 'trade+funds+holdings+positions',
    response_type: 'code'
  });

  // Component lifecycle logging
  useEffect(() => {
    console.log('🏦 useDhanIntegration hook mounted');
    console.log('🔗 Dhan OAuth Config:', dhanConfig);
    return () => console.log('🏦 useDhanIntegration hook unmounted');
  }, [dhanConfig]);

  // Fetch authoritative callback URLs from Engine C
  useEffect(() => {
    (async () => {
      try {
        const resp = await fetch(`${ENGINE_C_URL}/api/dhan/callback-urls`, { cache: 'no-store' });
        if (resp.ok) {
          const data = await resp.json();
          setDhanConfig(prev => ({
            ...prev,
            redirect_uri: data.redirect_url || prev.redirect_uri,
            postback_url: data.postback_url || prev.postback_url
          }));
        }
      } catch (e) {
        console.warn('Could not fetch callback URLs from Engine C:', e);
      }
    })();
  }, [ENGINE_C_URL]);

  // Check current Dhan connection status
  const checkConnectionStatus = useCallback(async () => {
    console.log('🔍 Checking Dhan connection status...');
    setConnectionStatus(prev => ({ ...prev, loading: true }));

    try {
      const response = await fetch(`${ENGINE_C_URL}/api/dhan/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'demo-token'}`
        },
        cache: 'no-store'
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Dhan status response:', data);
        
        setConnectionStatus({
          isConnected: data.connected || false,
          loading: false,
          error: null,
          accountDetails: data.account_details || null,
          lastUpdated: new Date().toISOString()
        });
      } else if (response.status === 404) {
        // Engine C not available, use demo status
        console.log('⚠️ Engine C not available, using demo status');
        setConnectionStatus({
          isConnected: false,
          loading: false,
          error: null,
          accountDetails: null,
          lastUpdated: new Date().toISOString()
        });
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('❌ Error checking Dhan connection status:', error);
      setConnectionStatus({
        isConnected: false,
        loading: false,
        error: error.message,
        accountDetails: null,
        lastUpdated: new Date().toISOString()
      });
    }
  }, [ENGINE_C_URL]);

  // Generate Dhan OAuth URL
  const generateAuthUrl = useCallback(() => {
    const state = `dhan_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const params = new URLSearchParams({
      client_id: dhanConfig.client_id,
      redirect_uri: dhanConfig.redirect_uri,
      response_type: dhanConfig.response_type,
      scope: dhanConfig.scope,
      state: state
    });

    const authUrl = `https://api.dhan.co/oauth/authorize?${params.toString()}`;
    
    console.log('🔐 Generated Dhan OAuth URL:', authUrl);
  console.log('🔗 Redirect URI:', dhanConfig.redirect_uri);
  console.log('🔄 Postback URL:', dhanConfig.postback_url);
    
    setAuthFlow({
      isInitiating: false,
      authUrl: authUrl,
      state: state,
      error: null
    });

    // Store state for validation
    localStorage.setItem('dhan_oauth_state', state);
    
    return authUrl;
  }, [dhanConfig]);

  // Initiate OAuth flow
  const initiateOAuth = useCallback(async () => {
    console.log('🚀 Initiating Dhan OAuth flow...');
    setAuthFlow(prev => ({ ...prev, isInitiating: true }));

    try {
      const authUrl = generateAuthUrl();
      
      // Open OAuth URL in new window/tab
      window.open(authUrl, '_blank', 'width=600,height=700,scrollbars=yes,resizable=yes');
      
      setAuthFlow(prev => ({
        ...prev,
        isInitiating: false
      }));

      return authUrl;
    } catch (error) {
      console.error('❌ Error initiating OAuth flow:', error);
      setAuthFlow(prev => ({
        ...prev,
        isInitiating: false,
        error: error.message
      }));
      throw error;
    }
  }, [generateAuthUrl]);

  // Handle OAuth callback (called from callback component)
  const handleOAuthCallback = useCallback(async (code, state, receivedState) => {
    console.log('🔄 Handling OAuth callback:', { code: code?.substr(0, 10) + '...', state, receivedState });

    // Validate state
    const storedState = localStorage.getItem('dhan_oauth_state');
    if (state !== storedState) {
      throw new Error('Invalid OAuth state parameter');
    }

    try {
      // Send authorization code to Engine C for token exchange
      const response = await fetch(`${ENGINE_C_URL}/api/dhan/callback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'demo-token'}`
        },
        body: JSON.stringify({
          code: code,
          state: state,
          redirect_uri: dhanConfig.redirect_uri,
          postback_url: dhanConfig.postback_url
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ OAuth callback successful:', data);
        
        // Refresh connection status
        await checkConnectionStatus();
        
        // Clear stored state
        localStorage.removeItem('dhan_oauth_state');
        
        return data;
      } else {
        throw new Error(`OAuth callback failed: ${response.status}`);
      }
    } catch (error) {
      console.error('❌ OAuth callback error:', error);
      throw error;
    }
  }, [ENGINE_C_URL, dhanConfig, checkConnectionStatus]);

  // Disconnect Dhan account
  const disconnectAccount = useCallback(async () => {
    console.log('🔌 Disconnecting Dhan account...');
    
    try {
      const response = await fetch(`${ENGINE_C_URL}/api/dhan/disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'demo-token'}`
        }
      });

      if (response.ok) {
        console.log('✅ Dhan account disconnected successfully');
        await checkConnectionStatus();
      } else {
        throw new Error(`Disconnect failed: ${response.status}`);
      }
    } catch (error) {
      console.error('❌ Error disconnecting Dhan account:', error);
      throw error;
    }
  }, [ENGINE_C_URL, checkConnectionStatus]);

  // Get OAuth URLs for chatbot
  const getOAuthUrls = useCallback(() => {
    const authUrl = generateAuthUrl();
    return {
      authUrl: authUrl,
      redirectUri: dhanConfig.redirect_uri,
      postbackUrl: dhanConfig.postback_url
    };
  }, [generateAuthUrl, dhanConfig]);

  // Initial status check
  useEffect(() => {
    checkConnectionStatus();
  }, [checkConnectionStatus]);

  return {
    // Connection status
    connectionStatus,
    
    // Auth flow state
    authFlow,
    
    // Actions
    initiateOAuth,
    handleOAuthCallback,
    disconnectAccount,
    checkConnectionStatus,
    getOAuthUrls,
    
    // Configuration
  config: dhanConfig,
    
    // URLs for reference
    urls: {
      frontend: FRONTEND_URL,
      engineC: ENGINE_C_URL,
      redirectUri: dhanConfig.redirect_uri,
      postbackUrl: dhanConfig.postback_url
    }
  };
};

export default useDhanIntegration;