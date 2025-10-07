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
  Clear
} from '@mui/icons-material';
import { format } from 'date-fns';

const ChatBot = ({ userId, apiUrl }) => {
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
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const inputRef = useRef(null);

useEffect(() => {
    // Connect to WebSocket for real-time chat
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userId, connectWebSocket]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    const wsUrl = `ws://localhost:8004/ws/${userId}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setConnected(true);
        console.log('Connected to chat WebSocket');
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnected(false);
      };
      
      wsRef.current.onclose = () => {
        setConnected(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      setConnected(false);
    }
  };

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
    
    if (connected && wsRef.current) {
      // Send via WebSocket
      wsRef.current.send(JSON.stringify({
        message: inputMessage,
        context: {
          timestamp: new Date().toISOString(),
          source: 'web_dashboard'
        }
      }));
    } else {
      // Fallback to HTTP API
      try {
        const response = await fetch(`${apiUrl.replace('8003', '8004')}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: userId,
            message: inputMessage,
            context: {
              timestamp: new Date().toISOString(),
              source: 'web_dashboard'
            }
          })
        });
        
        const data = await response.json();
        
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          type: 'assistant',
          message: data.message,
          timestamp: new Date(),
          intent: data.intent,
          data: data.data
        }]);
        
        setIsLoading(false);
      } catch (error) {
        console.error('Error sending message:', error);
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          type: 'assistant',
          message: "I'm having trouble connecting to the chat service. Please try again later.",
          timestamp: new Date(),
          intent: 'error'
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
              label={connected ? 'Connected' : 'Disconnected'} 
              size="small" 
              color={connected ? 'success' : 'error'} 
              sx={{ ml: 2 }}
            />
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