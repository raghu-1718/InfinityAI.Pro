import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  Chip,
  Avatar,
  Paper,
  Grid,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Refresh as RefreshIcon,
  AccountBalance as PortfolioIcon,
  TrendingUp as MarketIcon,
  Assessment as SignalsIcon,
  MonetizationOn as PnLIcon,
  AttachMoney as MoneyIcon
} from '@mui/icons-material';
import ApiService from '../services/ApiService';

const AIChatbot = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const quickCommands = [
    { command: '/portfolio', label: 'Portfolio', icon: <PortfolioIcon />, description: 'View your current portfolio' },
    { command: '/holdings', label: 'Holdings', icon: <MoneyIcon />, description: 'Check your holdings' },
    { command: '/pnl', label: 'P&L', icon: <PnLIcon />, description: 'Profit & Loss summary' },
    { command: '/market NSE', label: 'Market', icon: <MarketIcon />, description: 'NSE market overview' },
    { command: '/signals indian', label: 'Signals', icon: <SignalsIcon />, description: 'AI trading signals' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Welcome message
    const welcomeMessage = {
      id: Date.now(),
      text: `🙏 Namaste! I'm your InfinityAI assistant for Indian markets (NSE/BSE/MCX).\n\nI can help you with:\n• Portfolio management\n• Live market data\n• AI trading signals\n• P&L tracking\n\nTry quick commands like /portfolio, /holdings, or ask me anything about your investments!`,
      sender: 'bot',
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
    
    // Load chat history
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      const history = await ApiService.getChatHistory();
      if (history && history.messages) {
        const formattedMessages = history.messages.map(msg => ({
          id: msg.id || Date.now() + Math.random(),
          text: msg.message || msg.text,
          sender: msg.sender === 'user' ? 'user' : 'bot',
          timestamp: msg.timestamp || new Date().toISOString()
        }));
        setMessages(prev => [...prev, ...formattedMessages]);
      }
    } catch (err) {
      console.error('Error loading chat history:', err);
    }
  };

  const sendMessage = async (messageText = inputMessage) => {
    if (!messageText.trim() && !inputMessage.trim()) return;
    
    const userMessage = {
      id: Date.now(),
      text: messageText || inputMessage,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await ApiService.sendChatMessage(messageText || inputMessage);
      
      const botMessage = {
        id: Date.now() + 1,
        text: response.response || response.message || 'I received your message but couldn\'t process it properly. Please try again.',
        sender: 'bot',
        timestamp: new Date().toISOString(),
        data: response.data || null
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Engine D may be offline.');
      
      const errorMessage = {
        id: Date.now() + 1,
        text: '❌ Sorry, I\'m having trouble connecting to the server. Please try again in a moment.',
        sender: 'bot',
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setIsLoading(false);
  };

  const handleQuickCommand = (command) => {
    sendMessage(command);
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    const welcomeMessage = {
      id: Date.now(),
      text: '🔄 Chat cleared. How can I help you today?',
      sender: 'bot',
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  };

  const formatMessage = (message) => {
    if (message.data && typeof message.data === 'object') {
      // Format structured data
      if (message.data.portfolio) {
        return (
          <Box>
            <Typography variant="body1" gutterBottom>{message.text}</Typography>
            <Paper elevation={1} sx={{ p: 2, mt: 1 }}>
              <Typography variant="subtitle2" color="primary">Portfolio Summary</Typography>
              <Typography variant="body2">
                Total Value: {ApiService.formatINR(message.data.portfolio.total_value)}
              </Typography>
              <Typography variant="body2">
                Day P&L: {ApiService.formatINR(message.data.portfolio.day_pnl)} 
                ({ApiService.formatPercentage(message.data.portfolio.day_pnl_percent)})
              </Typography>
            </Paper>
          </Box>
        );
      }
    }
    
    // Regular text message with line breaks
    return message.text.split('\n').map((line, index) => (
      <Typography key={index} variant="body1" component="div">
        {line}
      </Typography>
    ));
  };

  return (
    <Box sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 3, pb: 0 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BotIcon color="primary" />
          InfinityAI Assistant
        </Typography>
        
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
          Chat with AI about your Indian market portfolio and trading strategies
        </Typography>

        {/* Quick Commands */}
        <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>Quick Commands:</Typography>
          <Grid container spacing={1}>
            {quickCommands.map((cmd) => (
              <Grid item key={cmd.command}>
                <Tooltip title={cmd.description}>
                  <Chip
                    icon={cmd.icon}
                    label={cmd.label}
                    onClick={() => handleQuickCommand(cmd.command)}
                    variant="outlined"
                    size="small"
                    sx={{ cursor: 'pointer' }}
                  />
                </Tooltip>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Box>

      {/* Chat Messages */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', px: 3 }}>
        <List sx={{ pb: 0 }}>
          {messages.map((message) => (
            <ListItem key={message.id} sx={{ flexDirection: 'column', alignItems: 'stretch', py: 1 }}>
              <Box sx={{ 
                display: 'flex', 
                justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                mb: 1
              }}>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    backgroundColor: message.sender === 'user' 
                      ? 'primary.main' 
                      : message.isError 
                        ? 'error.light'
                        : 'background.paper',
                    color: message.sender === 'user' 
                      ? 'primary.contrastText' 
                      : message.isError
                        ? 'error.contrastText'
                        : 'text.primary'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <Avatar
                      sx={{
                        width: 24,
                        height: 24,
                        bgcolor: message.sender === 'user' ? 'secondary.main' : 'primary.main'
                      }}
                    >
                      {message.sender === 'user' ? <PersonIcon fontSize="small" /> : <BotIcon fontSize="small" />}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      {formatMessage(message)}
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </Typography>
                </Paper>
              </Box>
            </ListItem>
          ))}
          {isLoading && (
            <ListItem>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Avatar sx={{ width: 24, height: 24 }}>
                  <BotIcon fontSize="small" />
                </Avatar>
                <Typography variant="body2" color="text.secondary">
                  InfinityAI is thinking...
                </Typography>
              </Box>
            </ListItem>
          )}
        </List>
        <div ref={messagesEndRef} />
      </Box>

      {/* Chat Input */}
      <Box sx={{ p: 3, pt: 1 }}>
        <Card elevation={2}>
          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder="Ask about your portfolio, market trends, or type a command like /portfolio..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                size="small"
              />
              <Button
                variant="contained"
                onClick={() => sendMessage()}
                disabled={isLoading || !inputMessage.trim()}
                sx={{ minWidth: 'auto', p: 1 }}
              >
                <SendIcon />
              </Button>
              <IconButton onClick={clearChat} size="small">
                <RefreshIcon />
              </IconButton>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default AIChatbot;