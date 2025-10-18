import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  Clear,
  Notifications,
  AccountBalance,
  TrendingUp
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useChatbotStatus, useWebSocket } from '../../hooks/useEngineData';
import { useDhanIntegration } from '../../hooks/useDhanIntegration';

const ChatBot = ({ userId, apiUrl }) => {
  console.log('🤖 ChatBot component mounted with userId:', userId);
  
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      message: "👋 Hi! I'm your InfinityAI trading assistant. I can help you with portfolio queries, market analysis, trading decisions, and AI insights. Try asking me something like 'Show my portfolio' or 'Analyze TSLA'!",
      timestamp: new Date(),
      intent: 'help'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);
  
  // Use Engine D hooks
  const { data: chatbotData, loading: chatbotLoading, error: chatbotError } = useChatbotStatus(30000);
  const { isConnected, messages: wsMessages, sendMessage: wsSendMessage, error: wsError } = useWebSocket('D', `/ws/${userId}`);
  
  // Use Dhan integration for OAuth flow
  const { connectionStatus, getOAuthUrls } = useDhanIntegration();
  
  // Debug logging for connection status
  useEffect(() => {
    console.log('🔗 ChatBot WebSocket connection status:', isConnected);
    console.log('📡 ChatBot service data:', chatbotData);
    console.log('⚠️ ChatBot errors:', { chatbotError, wsError });
  }, [isConnected, chatbotData, chatbotError, wsError]);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Handle WebSocket messages from Engine D
  useEffect(() => {
    if (wsMessages.length > 0) {
      const latestMessage = wsMessages[wsMessages.length - 1];
      console.log('Received WebSocket message:', latestMessage);
      
      // Handle different message types from Engine D
      if (latestMessage.data?.type === 'chat_response' || latestMessage.data?.message_id) {
        setMessages(prev => [...prev, {
          id: Date.now(),
          type: 'assistant',
          message: latestMessage.data.response || latestMessage.data.message || 'I received your message.',
          timestamp: new Date(latestMessage.timestamp),
          intent: latestMessage.data.intent || 'general',
          confidence: latestMessage.data.confidence
        }]);
        setIsLoading(false);
      } else if (latestMessage.data?.type === 'ai_signal' || latestMessage.data?.type === 'price_alert') {
        // Handle real-time notifications
        setNotifications(prev => [...prev.slice(-4), {
          id: Date.now(),
          type: latestMessage.data.type,
          data: latestMessage.data,
          timestamp: new Date(latestMessage.timestamp)
        }]);
      } else {
        // Generic message handling
        console.log('Unhandled WebSocket message type:', latestMessage.data);
      }
    }
  }, [wsMessages]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    scrollToBottom();
  }, [messages]);

  const handleWebSocketMessage = (data) => {
    if (data.type === 'chat_response') {
      const response = data.data;
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: 'assistant',
        message: response.message,
        timestamp: new Date(),
        intent: response.intent,
        data: response.data
      }]);
      setIsLoading(false);
    } else if (data.type === 'price_alert' || data.type === 'ai_signal' || data.type === 'order_update') {
      // Handle real-time notifications
      setNotifications(prev => [...prev, {
        id: Date.now(),
        type: data.type,
        data: data.data,
        timestamp: new Date()
      }]);
      
      // Add notification as chat message
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: 'notification',
        message: data.data.message,
        timestamp: new Date(),
        intent: data.type,
        data: data.data
      }]);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage = {
      id: Date.now(),
      type: 'user',
      message: inputMessage,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    // Check for Dhan connection requests
    const lowerMessage = inputMessage.toLowerCase();
    const isDhanConnectionRequest = 
      lowerMessage.includes('connect') && lowerMessage.includes('dhan') ||
      lowerMessage.includes('dhan') && lowerMessage.includes('account') ||
      lowerMessage.includes('link') && lowerMessage.includes('dhan') ||
      lowerMessage.includes('setup') && lowerMessage.includes('dhan') ||
      lowerMessage.includes('integrate') && lowerMessage.includes('dhan') ||
      lowerMessage.includes('broker') && lowerMessage.includes('connect');
    
    if (isDhanConnectionRequest) {
      console.log('🎆 Dhan connection request detected via chatbot');
      handleDhanConnectionRequest();
      return;
    }
    
    if (isConnected) {
      // Send via WebSocket using the hook
      console.log('Sending WebSocket message:', inputMessage);
      const success = wsSendMessage({
        message: inputMessage,
        user_id: userId,
        context: {
          timestamp: new Date().toISOString(),
          source: 'web_dashboard'
        }
      });
      
      if (!success) {
        setIsLoading(false);
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          type: 'assistant',
          message: "Failed to send message via WebSocket. Please try again.",
          timestamp: new Date(),
          intent: 'error'
        }]);
      }
    } else {
      // Fallback to HTTP API using Engine D URL
      console.log('WebSocket not connected, using HTTP fallback');
      try {
        const engineDUrl = process.env.REACT_APP_ENGINE_D_URL || 'https://engine-d-chatbot-573866363639.us-central1.run.app';
        console.log('Sending HTTP request to:', `${engineDUrl}/api/chat`);
        
        const response = await fetch(`${engineDUrl}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          cache: 'no-store',
          body: JSON.stringify({
            user_id: userId,
            message: inputMessage
          })
        });
        
        console.log('HTTP Response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('HTTP Response data:', data);
          
          setMessages(prev => [...prev, {
            id: Date.now() + 1,
            type: 'assistant',
            message: data.response || data.message || `I received your message: "${inputMessage}" - This is a demo response since the AI service is processing your request.`,
            timestamp: new Date(),
            intent: data.intent || 'general',
            confidence: data.confidence
          }]);
        } else if (response.status === 405 || response.status === 400) {
          // Handle method not allowed or bad request
          console.log('HTTP method issue, using demo response');
          setMessages(prev => [...prev, {
            id: Date.now() + 1,
            type: 'assistant',
            message: `I understand you're asking: "${inputMessage}". The chat API is currently being optimized. I'm here to help with portfolio management, market analysis, and AI insights!`,
            timestamp: new Date(),
            intent: 'demo_response'
          }]);
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error('Error sending message to Engine D:', error);
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          type: 'assistant',
          message: `I see you said: "${inputMessage}". I'm currently experiencing connection issues but I'm working on getting back online. Try asking about your portfolio or market analysis!`,
          timestamp: new Date(),
          intent: 'connection_error'
        }]);
        setIsLoading(false);
      }
    }
    
    setInputMessage('');
    inputRef.current?.focus();
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };
  
  // Handle Dhan connection requests through chatbot
  const handleDhanConnectionRequest = () => {
    try {
      const { authUrl, redirectUri, postbackUrl } = getOAuthUrls();
      
      const responseMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        message: `I'll help you connect your Dhan trading account! 🎆

🔗 **OAuth Authorization URL:**
${authUrl}

🔄 **Redirect URL:** ${redirectUri}
🔌 **Postback URL:** ${postbackUrl}

**Instructions:**
1. Click the authorization URL above to open Dhan's login page
2. Login with your Dhan credentials
3. Grant permissions to InfinityAI.Pro
4. You'll be automatically redirected back to the dashboard

**Or** you can also connect through the "Broker Integration" tab in the dashboard.

Would you like me to open the authorization page for you?`,
        timestamp: new Date(),
        intent: 'dhan_connection',
        data: {
          authUrl,
          redirectUri,
          postbackUrl,
          isConnected: connectionStatus.isConnected
        }
      };
      
      setMessages(prev => [...prev, responseMessage]);
      setIsLoading(false);
      
      // Add a follow-up message with an action button
      setTimeout(() => {
        const actionMessage = {
          id: Date.now() + 2,
          type: 'assistant',
          message: 'Ready to connect? Click the button below to start the OAuth flow!',
          timestamp: new Date(),
          intent: 'dhan_action',
          data: {
            action: 'open_oauth',
            authUrl: authUrl
          }
        };
        setMessages(prev => [...prev, actionMessage]);
      }, 1000);
      
    } catch (error) {
      console.error('❌ Error generating Dhan OAuth URLs:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        message: `Sorry, I encountered an error while setting up the Dhan connection: ${error.message}

Please try connecting through the "Broker Integration" tab in the dashboard instead.`,
        timestamp: new Date(),
        intent: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };
  
  // Handle OAuth URL opening
  const handleOpenOAuth = (authUrl) => {
    console.log('🚀 Opening Dhan OAuth URL from chatbot:', authUrl);
    window.open(authUrl, '_blank', 'width=600,height=700,scrollbars=yes,resizable=yes');
    
    const confirmMessage = {
      id: Date.now(),
      type: 'assistant',
      message: 'OAuth window opened! Please complete the authentication in the new window. Once you\'re done, your account will be connected automatically. ✨',
      timestamp: new Date(),
      intent: 'oauth_opened'
    };
    setMessages(prev => [...prev, confirmMessage]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const clearChat = () => {
    setMessages([{
      id: Date.now(),
      type: 'assistant',
      message: "Chat cleared! How can I help you with your trading today?",
      timestamp: new Date(),
      intent: 'help'
    }]);
    setNotifications([]);
  };

  const getMessageIcon = (type, intent) => {
    if (type === 'user') return <Person />;
    if (type === 'notification') return <Notifications />;
    if (intent === 'portfolio_query') return <AccountBalance />;
    if (intent === 'market_analysis') return <TrendingUp />;
    return <SmartToy />;
  };

  const getMessageColor = (type, intent) => {
    if (type === 'user') return 'primary';
    if (type === 'notification') return 'warning';
    if (intent === 'error') return 'error';
    if (intent === 'portfolio_query') return 'success';
    if (intent === 'market_analysis') return 'info';
    return 'secondary';
  };

  const formatMessage = (message, data) => {
    // Handle markdown-like formatting in messages
    return message.split('\n').map((line, index) => (
      <Typography 
        key={index}
        variant={line.startsWith('**') ? 'subtitle2' : 'body2'}
        component="div"
        sx={{ 
          fontWeight: line.startsWith('**') ? 'bold' : 'normal',
          mt: index > 0 ? 0.5 : 0
        }}
      >
        {line.replace(/\*\*/g, '')}
      </Typography>
    ));
  };

  const quickActions = [
    { label: "Show my portfolio", icon: <AccountBalance /> },
    { label: "Analyze AAPL", icon: <TrendingUp /> },
    { label: "Latest economic events", icon: <Notifications /> },
    { label: "AI model status", icon: <SmartToy /> },
    { label: "Help", icon: <SmartToy /> }
  ];

  return (
    <Box sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SmartToy color="secondary" sx={{ mr: 1 }} />
            <Typography variant="h6">
              AI Trading Assistant
            </Typography>
            <Chip 
              label={isConnected ? 'Connected' : 'Disconnected'} 
              size="small" 
              color={isConnected ? 'success' : 'error'} 
              sx={{ ml: 2 }}
            />
            {chatbotError && (
              <Chip 
                label="Service Error" 
                size="small" 
                color="warning" 
                sx={{ ml: 1 }}
              />
            )}
          </Box>
          <Tooltip title="Clear Chat">
            <IconButton onClick={clearChat} size="small">
              <Clear />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Notifications */}
      {notifications.slice(-2).map((notification) => (
        <Alert 
          key={notification.id}
          severity="info"
          sx={{ m: 1 }}
          onClose={() => setNotifications(prev => 
            prev.filter(n => n.id !== notification.id)
          )}
        >
          <strong>{notification.type.replace('_', ' ').toUpperCase()}:</strong> {notification.data.message}
        </Alert>
      ))}

      {/* Messages */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 1 }}>
        <List>
          {messages.map((msg) => (
            <ListItem 
              key={msg.id}
              sx={{ 
                mb: 1, 
                alignItems: 'flex-start',
                flexDirection: msg.type === 'user' ? 'row-reverse' : 'row'
              }}
            >
              <Avatar 
                sx={{ 
                  bgcolor: getMessageColor(msg.type, msg.intent) + '.main',
                  mr: msg.type === 'user' ? 0 : 1,
                  ml: msg.type === 'user' ? 1 : 0,
                  width: 32,
                  height: 32
                }}
              >
                {getMessageIcon(msg.type, msg.intent)}
              </Avatar>
              
              <Paper
                sx={{
                  p: 2,
                  bgcolor: msg.type === 'user' ? 'primary.light' : 'background.paper',
                  color: msg.type === 'user' ? 'primary.contrastText' : 'text.primary',
                  maxWidth: '70%',
                  borderRadius: 2
                }}
              >
                <Box>
                  {formatMessage(msg.message, msg.data)}
                  
                  {/* Display additional data if available */}
                  {msg.data && msg.intent === 'portfolio_query' && (
                    <Box sx={{ mt: 1 }}>
                      <Chip label={`${msg.data.positions?.length || 0} positions`} size="small" />
                    </Box>
                  )}
                  
                  {/* Dhan OAuth Action Button */}
                  {msg.intent === 'dhan_action' && msg.data?.action === 'open_oauth' && (
                    <Box sx={{ mt: 2 }}>
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<AccountBalance />}
                        onClick={() => handleOpenOAuth(msg.data.authUrl)}
                        fullWidth
                      >
                        Connect Dhan Account
                      </Button>
                    </Box>
                  )}
                  
                  <Typography 
                    variant="caption" 
                    color="text.secondary" 
                    sx={{ display: 'block', mt: 1 }}
                  >
                    {format(msg.timestamp, 'HH:mm:ss')}
                  </Typography>
                </Box>
              </Paper>
            </ListItem>
          ))}
          
          {isLoading && (
            <ListItem>
              <Avatar sx={{ bgcolor: 'secondary.main', mr: 1, width: 32, height: 32 }}>
                <SmartToy />
              </Avatar>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  AI is thinking...
                </Typography>
              </Box>
            </ListItem>
          )}
        </List>
        <div ref={messagesEndRef} />
      </Box>

      {/* Quick Actions */}
      <Box sx={{ p: 1, borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          Quick Actions:
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {quickActions.map((action, index) => (
            <Chip
              key={index}
              icon={action.icon}
              label={action.label}
              size="small"
              clickable
              onClick={() => setInputMessage(action.label)}
              variant="outlined"
            />
          ))}
        </Box>
      </Box>

      {/* Input */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={3}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about your portfolio, market analysis, AI insights, or trading decisions..."
            variant="outlined"
            size="small"
          />
          <Button
            variant="contained"
            endIcon={<Send />}
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
          >
            Send
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatBot;