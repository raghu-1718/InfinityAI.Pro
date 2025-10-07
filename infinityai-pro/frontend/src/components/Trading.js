import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Autocomplete,
  Tabs,
  Tab,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Send,
  Cancel,
  History,
  Refresh
} from '@mui/icons-material';

const Trading = ({ apiUrl, userId }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [orderForm, setOrderForm] = useState({
    symbol: '',
    side: 'buy',
    quantity: '',
    order_type: 'market',
    price: '',
    time_in_force: 'day'
  });
  const [orders, setOrders] = useState([]);
  const [positions, setPositions] = useState([]);
  const [quotes, setQuotes] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState('');
  const [confirmDialog, setConfirmDialog] = useState({ open: false, order: null });
  const [symbolSuggestions, setSymbolSuggestions] = useState([]);
  const [searchSymbol, setSearchSymbol] = useState('');

  // Popular symbols for suggestions
  const popularSymbols = [
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
    'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'PYPL', 'DIS', 'V',
    'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'ARKK', 'GLD', 'SLV'
  ];

  // Fetch data on component mount
useEffect(() => {
    fetchOrders();
    fetchPositions();
    connectWebSocket();
  }, [connectWebSocket, fetchOrders, fetchPositions]);

  // Connect to WebSocket for real-time updates
  const connectWebSocket = useCallback(() => {
    const wsUrl = `ws://localhost:8003/ws/trading/${userId}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('Trading WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'quote_update') {
          setQuotes(prev => ({
            ...prev,
            [data.symbol]: data.quote
          }));
        } else if (data.type === 'order_update') {
          setOrders(prev => 
            prev.map(order => 
              order.id === data.order.id ? data.order : order
            )
          );
        } else if (data.type === 'position_update') {
          setPositions(prev => 
            prev.map(pos => 
              pos.symbol === data.position.symbol ? data.position : pos
            )
          );
        }
      };
      
      ws.onerror = (error) => {
        console.error('Trading WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('Trading WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      return ws;
    } catch (error) {
      console.error('Failed to connect to trading WebSocket:', error);
    }
  }, [userId]);

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${apiUrl}/orders`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders || []);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const fetchPositions = async () => {
    try {
      const response = await fetch(`${apiUrl}/portfolio`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPositions(data.positions || []);
      }
    } catch (error) {
      console.error('Error fetching positions:', error);
    }
  };

  const fetchQuote = async (symbol) => {
    try {
      const response = await fetch(`${apiUrl}/quote/${symbol}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setQuotes(prev => ({
          ...prev,
          [symbol]: data
        }));
        return data;
      }
    } catch (error) {
      console.error(`Error fetching quote for ${symbol}:`, error);
    }
  };

  const handleOrderSubmit = async () => {
    setSubmitLoading(true);
    setError(null);
    setSuccess('');

    try {
      const orderData = {
        ...orderForm,
        quantity: parseInt(orderForm.quantity),
        price: orderForm.order_type === 'limit' ? parseFloat(orderForm.price) : undefined
      };

      const response = await fetch(`${apiUrl}/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(orderData)
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(`Order submitted successfully! Order ID: ${data.order_id}`);
        setOrderForm({
          symbol: '',
          side: 'buy',
          quantity: '',
          order_type: 'market',
          price: '',
          time_in_force: 'day'
        });
        fetchOrders(); // Refresh orders list
        setConfirmDialog({ open: false, order: null });
      } else {
        setError(data.error || 'Failed to submit order');
      }
    } catch (error) {
      setError('Error submitting order: ' + error.message);
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleCancelOrder = async (orderId) => {
    try {
      const response = await fetch(`${apiUrl}/orders/${orderId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        setSuccess('Order cancelled successfully');
        fetchOrders();
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to cancel order');
      }
    } catch (error) {
      setError('Error cancelling order: ' + error.message);
    }
  };

  const handleSymbolSearch = async (value) => {
    setSearchSymbol(value);
    
    if (value.length >= 2) {
      // Filter popular symbols and add search results
      const filtered = popularSymbols.filter(symbol => 
        symbol.includes(value.toUpperCase())
      );
      setSymbolSuggestions(filtered);
    } else {
      setSymbolSuggestions(popularSymbols.slice(0, 10));
    }
  };

  const handleSymbolSelect = async (symbol) => {
    setOrderForm(prev => ({ ...prev, symbol }));
    if (symbol) {
      await fetchQuote(symbol);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const getOrderStatusChip = (status) => {
    const statusColors = {
      'pending': 'warning',
      'filled': 'success',
      'cancelled': 'error',
      'rejected': 'error',
      'partial': 'info'
    };
    
    return (
      <Chip 
        label={status.toUpperCase()} 
        color={statusColors[status] || 'default'} 
        size="small" 
      />
    );
  };

  const getOrderIcon = (status) => {
    switch (status) {
      case 'filled': return <CheckCircle color="success" />;
      case 'cancelled': 
      case 'rejected': return <ErrorOutline color="error" />;
      default: return <Schedule color="warning" />;
    }
  };

  const calculateOrderValue = () => {
    const quantity = parseInt(orderForm.quantity) || 0;
    const symbol = orderForm.symbol;
    
    if (orderForm.order_type === 'market' && quotes[symbol]) {
      const price = orderForm.side === 'buy' ? quotes[symbol].ask : quotes[symbol].bid;
      return quantity * price;
    } else if (orderForm.order_type === 'limit' && orderForm.price) {
      return quantity * parseFloat(orderForm.price);
    }
    
    return 0;
  };

  const canSubmitOrder = () => {
    return orderForm.symbol && 
           orderForm.quantity && 
           parseInt(orderForm.quantity) > 0 &&
           (orderForm.order_type === 'market' || (orderForm.order_type === 'limit' && orderForm.price));
  };

  const getCurrentQuote = (symbol) => {
    return quotes[symbol] || null;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>
        Trading Center
      </Typography>

      {/* Alert Messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Place Order" icon={<Send />} />
        <Tab label="Open Orders" icon={<Schedule />} />
        <Tab label="Order History" icon={<History />} />
      </Tabs>

      {/* Place Order Tab */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  New Order
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Autocomplete
                      value={orderForm.symbol}
                      onChange={(event, newValue) => handleSymbolSelect(newValue)}
                      inputValue={searchSymbol}
                      onInputChange={(event, newInputValue) => handleSymbolSearch(newInputValue)}
                      options={symbolSuggestions}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="Symbol"
                          variant="outlined"
                          fullWidth
                          placeholder="Search symbols (e.g., AAPL)"
                        />
                      )}
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Side</InputLabel>
                      <Select
                        value={orderForm.side}
                        onChange={(e) => setOrderForm(prev => ({ ...prev, side: e.target.value }))}
                        label="Side"
                      >
                        <MenuItem value="buy">Buy</MenuItem>
                        <MenuItem value="sell">Sell</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="Quantity"
                      type="number"
                      value={orderForm.quantity}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, quantity: e.target.value }))}
                      fullWidth
                      variant="outlined"
                      placeholder="Enter number of shares"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Order Type</InputLabel>
                      <Select
                        value={orderForm.order_type}
                        onChange={(e) => setOrderForm(prev => ({ 
                          ...prev, 
                          order_type: e.target.value,
                          price: e.target.value === 'market' ? '' : prev.price
                        }))}
                        label="Order Type"
                      >
                        <MenuItem value="market">Market</MenuItem>
                        <MenuItem value="limit">Limit</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  {orderForm.order_type === 'limit' && (
                    <Grid item xs={12} md={6}>
                      <TextField
                        label="Limit Price"
                        type="number"
                        value={orderForm.price}
                        onChange={(e) => setOrderForm(prev => ({ ...prev, price: e.target.value }))}
                        fullWidth
                        variant="outlined"
                        placeholder="Enter limit price"
                        inputProps={{ step: "0.01" }}
                      />
                    </Grid>
                  )}
                  
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Time in Force</InputLabel>
                      <Select
                        value={orderForm.time_in_force}
                        onChange={(e) => setOrderForm(prev => ({ ...prev, time_in_force: e.target.value }))}
                        label="Time in Force"
                      >
                        <MenuItem value="day">Day</MenuItem>
                        <MenuItem value="gtc">Good Till Cancelled</MenuItem>
                        <MenuItem value="ioc">Immediate or Cancel</MenuItem>
                        <MenuItem value="fok">Fill or Kill</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 3 }} />
                
                {/* Order Summary */}
                <Box sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1, mb: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    Order Summary
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Order Value:
                      </Typography>
                      <Typography variant="h6">
                        {formatCurrency(calculateOrderValue())}
                      </Typography>
                    </Grid>
                    {orderForm.symbol && getCurrentQuote(orderForm.symbol) && (
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Current Price:
                        </Typography>
                        <Typography variant="h6">
                          {formatCurrency(getCurrentQuote(orderForm.symbol).last || 0)}
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </Box>
                
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={() => setConfirmDialog({ open: true, order: orderForm })}
                  disabled={!canSubmitOrder() || submitLoading}
                  sx={{ mt: 2 }}
                >
                  {submitLoading ? 'Submitting...' : `${orderForm.side.toUpperCase()} ${orderForm.quantity || 0} ${orderForm.symbol || 'SYMBOL'}`}
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            {/* Real-time Quote */}
            {orderForm.symbol && getCurrentQuote(orderForm.symbol) && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    {orderForm.symbol} Quote
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Last</Typography>
                      <Typography variant="h5">
                        {formatCurrency(getCurrentQuote(orderForm.symbol).last)}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Change</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography 
                          variant="h6" 
                          sx={{ 
                            color: getCurrentQuote(orderForm.symbol).change >= 0 ? 'success.main' : 'error.main' 
                          }}
                        >
                          {getCurrentQuote(orderForm.symbol).change >= 0 ? '+' : ''}
                          {getCurrentQuote(orderForm.symbol).change?.toFixed(2)}
                        </Typography>
                        {getCurrentQuote(orderForm.symbol).change >= 0 ? <TrendingUp color="success" /> : <TrendingDown color="error" />}
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Bid</Typography>
                      <Typography variant="body1">
                        {formatCurrency(getCurrentQuote(orderForm.symbol).bid)} x {getCurrentQuote(orderForm.symbol).bid_size}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Ask</Typography>
                      <Typography variant="body1">
                        {formatCurrency(getCurrentQuote(orderForm.symbol).ask)} x {getCurrentQuote(orderForm.symbol).ask_size}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}
            
            {/* Quick Actions */}
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Quick Actions
                </Typography>
                
                <Grid container spacing={1}>
                  {popularSymbols.slice(0, 6).map((symbol) => (
                    <Grid item xs={6} key={symbol}>
                      <Button
                        variant="outlined"
                        size="small"
                        fullWidth
                        onClick={() => handleSymbolSelect(symbol)}
                      >
                        {symbol}
                      </Button>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Open Orders Tab */}
      {activeTab === 1 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Open Orders</Typography>
              <IconButton onClick={fetchOrders}>
                <Refresh />
              </IconButton>
            </Box>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell align="right">Filled</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Time</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {orders.filter(order => ['pending', 'partial'].includes(order.status)).map((order) => (
                    <TableRow key={order.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                          {order.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={order.side.toUpperCase()}
                          color={order.side === 'buy' ? 'success' : 'error'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{order.order_type.toUpperCase()}</TableCell>
                      <TableCell align="right">{order.quantity.toLocaleString()}</TableCell>
                      <TableCell align="right">
                        {order.order_type === 'market' ? 'MKT' : formatCurrency(order.price)}
                      </TableCell>
                      <TableCell align="right">{order.filled_quantity || 0}</TableCell>
                      <TableCell>{getOrderStatusChip(order.status)}</TableCell>
                      <TableCell>
                        {new Date(order.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell align="center">
                        {['pending', 'partial'].includes(order.status) && (
                          <Tooltip title="Cancel Order">
                            <IconButton
                              size="small"
                              onClick={() => handleCancelOrder(order.id)}
                              color="error"
                            >
                              <Cancel />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {orders.filter(order => ['pending', 'partial'].includes(order.status)).length === 0 && (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography color="text.secondary">
                    No open orders
                  </Typography>
                </Box>
              )}
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Order History Tab */}
      {activeTab === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Order History</Typography>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell align="right">Filled</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Time</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {orders.map((order) => (
                    <TableRow key={order.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {getOrderIcon(order.status)}
                          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', ml: 1 }}>
                            {order.symbol}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={order.side.toUpperCase()}
                          color={order.side === 'buy' ? 'success' : 'error'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{order.order_type.toUpperCase()}</TableCell>
                      <TableCell align="right">{order.quantity.toLocaleString()}</TableCell>
                      <TableCell align="right">
                        {order.order_type === 'market' ? 'MKT' : formatCurrency(order.price || 0)}
                      </TableCell>
                      <TableCell align="right">{order.filled_quantity || 0}</TableCell>
                      <TableCell>{getOrderStatusChip(order.status)}</TableCell>
                      <TableCell>
                        {new Date(order.created_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {orders.length === 0 && (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography color="text.secondary">
                    No order history
                  </Typography>
                </Box>
              )}
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Order Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, order: null })}>
        <DialogTitle>Confirm Order</DialogTitle>
        <DialogContent>
          {confirmDialog.order && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {confirmDialog.order.side.toUpperCase()} {confirmDialog.order.quantity} {confirmDialog.order.symbol}
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Order Type:</Typography>
                  <Typography>{confirmDialog.order.order_type.toUpperCase()}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Time in Force:</Typography>
                  <Typography>{confirmDialog.order.time_in_force.toUpperCase()}</Typography>
                </Grid>
                {confirmDialog.order.order_type === 'limit' && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Limit Price:</Typography>
                    <Typography>{formatCurrency(parseFloat(confirmDialog.order.price))}</Typography>
                  </Grid>
                )}
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Estimated Value:</Typography>
                  <Typography variant="h6">{formatCurrency(calculateOrderValue())}</Typography>
                </Grid>
              </Grid>
              
              <Alert severity="info" sx={{ mt: 2 }}>
                Please review your order details carefully before submitting.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, order: null })}>
            Cancel
          </Button>
          <Button 
            onClick={handleOrderSubmit} 
            variant="contained" 
            disabled={submitLoading}
          >
            {submitLoading ? <LinearProgress /> : 'Submit Order'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Trading;