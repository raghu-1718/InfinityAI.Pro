import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  Divider,
  Alert
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  AccountBalance,
  ShowChart,
  Info,
  Close as CloseIcon
} from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line, Area, AreaChart } from 'recharts';

const Portfolio = ({ apiUrl, userId }) => {
  const [portfolioData, setPortfolioData] = useState(null);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [ws, setWs] = useState(null);

  // Fetch portfolio data
  const fetchPortfolioData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/portfolio`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch portfolio data');
      
      const data = await response.json();
      setPortfolioData(data.portfolio);
      setPositions(data.positions || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching portfolio:', err);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  // Connect to WebSocket for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `ws://localhost:8003/ws/portfolio/${userId}`;
      
      try {
        const websocket = new WebSocket(wsUrl);
        
        websocket.onopen = () => {
          console.log('Portfolio WebSocket connected');
          setWs(websocket);
        };
        
        websocket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'portfolio_update') {
            setPortfolioData(prev => ({
              ...prev,
              ...data.portfolio
            }));
          } else if (data.type === 'position_update') {
            setPositions(prev => 
              prev.map(pos => 
                pos.symbol === data.position.symbol 
                  ? { ...pos, ...data.position }
                  : pos
              )
            );
          }
        };
        
        websocket.onerror = (error) => {
          console.error('Portfolio WebSocket error:', error);
        };
        
        websocket.onclose = () => {
          console.log('Portfolio WebSocket disconnected');
          // Attempt to reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };
        
        return websocket;
      } catch (error) {
        console.error('Failed to connect to portfolio WebSocket:', error);
      }
    };

    const websocket = connectWebSocket();
    
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [userId]);

  useEffect(() => {
    fetchPortfolioData();
  }, [fetchPortfolioData]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getPerformanceColor = (value) => {
    return value >= 0 ? 'success.main' : 'error.main';
  };

  const getPerformanceIcon = (value) => {
    return value >= 0 ? <TrendingUp /> : <TrendingDown />;
  };

  // Prepare data for charts
  const prepareAllocationData = () => {
    return positions.map(pos => ({
      name: pos.symbol,
      value: pos.market_value,
      percentage: ((pos.market_value / portfolioData?.total_value) * 100).toFixed(1)
    }));
  };

  const prepareSectorData = () => {
    const sectorMap = {};
    positions.forEach(pos => {
      const sector = pos.sector || 'Other';
      if (sectorMap[sector]) {
        sectorMap[sector] += pos.market_value;
      } else {
        sectorMap[sector] = pos.market_value;
      }
    });
    
    return Object.keys(sectorMap).map(sector => ({
      name: sector,
      value: sectorMap[sector],
      percentage: ((sectorMap[sector] / portfolioData?.total_value) * 100).toFixed(1)
    }));
  };

  const preparePerformanceData = () => {
    return positions.map(pos => ({
      symbol: pos.symbol,
      dailyPnL: pos.unrealized_pnl_daily || 0,
      totalPnL: pos.unrealized_pnl || 0,
      dailyReturn: ((pos.unrealized_pnl_daily || 0) / pos.market_value * 100).toFixed(2)
    }));
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658'];

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
          Loading Portfolio Data...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 3 }}>
        Error loading portfolio: {error}
        <Button onClick={fetchPortfolioData} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          Portfolio Overview
        </Typography>
        <Box>
          <Tooltip title="Refresh Data">
            <IconButton onClick={fetchPortfolioData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Portfolio Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                Total Value
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(portfolioData?.total_value || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                Cash Balance
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(portfolioData?.cash_balance || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                Daily P&L
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    fontWeight: 'bold',
                    color: getPerformanceColor(portfolioData?.daily_pnl || 0)
                  }}
                >
                  {formatCurrency(portfolioData?.daily_pnl || 0)}
                </Typography>
                {getPerformanceIcon(portfolioData?.daily_pnl || 0)}
              </Box>
              <Typography 
                variant="body2" 
                sx={{ color: getPerformanceColor(portfolioData?.daily_return || 0) }}
              >
                {formatPercentage(portfolioData?.daily_return || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                Total P&L
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    fontWeight: 'bold',
                    color: getPerformanceColor(portfolioData?.total_pnl || 0)
                  }}
                >
                  {formatCurrency(portfolioData?.total_pnl || 0)}
                </Typography>
                {getPerformanceIcon(portfolioData?.total_pnl || 0)}
              </Box>
              <Typography 
                variant="body2" 
                sx={{ color: getPerformanceColor(portfolioData?.total_return || 0) }}
              >
                {formatPercentage(portfolioData?.total_return || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Portfolio Allocation
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={prepareAllocationData()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percentage }) => `${name}: ${percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {prepareAllocationData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip formatter={(value) => [formatCurrency(value), 'Value']} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Sector Allocation
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={prepareSectorData()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percentage }) => `${name}: ${percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {prepareSectorData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip formatter={(value) => [formatCurrency(value), 'Value']} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Chart */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Position Performance
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={preparePerformanceData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="symbol" />
              <YAxis />
              <RechartsTooltip formatter={(value) => [formatCurrency(value), 'P&L']} />
              <Bar dataKey="dailyPnL" fill="#8884d8" name="Daily P&L" />
              <Bar dataKey="totalPnL" fill="#82ca9d" name="Total P&L" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Positions Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Current Positions
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Symbol</TableCell>
                  <TableCell align="right">Quantity</TableCell>
                  <TableCell align="right">Avg Cost</TableCell>
                  <TableCell align="right">Current Price</TableCell>
                  <TableCell align="right">Market Value</TableCell>
                  <TableCell align="right">Daily P&L</TableCell>
                  <TableCell align="right">Total P&L</TableCell>
                  <TableCell align="right">Daily Return</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {positions.map((position) => (
                  <TableRow key={position.symbol} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                          {position.symbol}
                        </Typography>
                        {position.sector && (
                          <Chip 
                            label={position.sector} 
                            size="small" 
                            sx={{ ml: 1 }} 
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      {position.quantity.toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(position.avg_cost)}
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(position.current_price)}
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(position.market_value)}
                    </TableCell>
                    <TableCell 
                      align="right"
                      sx={{ color: getPerformanceColor(position.unrealized_pnl_daily || 0) }}
                    >
                      {formatCurrency(position.unrealized_pnl_daily || 0)}
                    </TableCell>
                    <TableCell 
                      align="right"
                      sx={{ color: getPerformanceColor(position.unrealized_pnl || 0) }}
                    >
                      {formatCurrency(position.unrealized_pnl || 0)}
                    </TableCell>
                    <TableCell 
                      align="right"
                      sx={{ color: getPerformanceColor(position.daily_return || 0) }}
                    >
                      {formatPercentage(position.daily_return || 0)}
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="View Details">
                        <IconButton 
                          size="small"
                          onClick={() => {
                            setSelectedPosition(position);
                            setDetailsOpen(true);
                          }}
                        >
                          <Info />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Position Details Dialog */}
      <Dialog 
        open={detailsOpen} 
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {selectedPosition?.symbol} - Position Details
            </Typography>
            <IconButton onClick={() => setDetailsOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedPosition && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Position Size</Typography>
                <Typography variant="h6">{selectedPosition.quantity.toLocaleString()} shares</Typography>
                
                <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Average Cost Basis</Typography>
                <Typography variant="h6">{formatCurrency(selectedPosition.avg_cost)}</Typography>
                
                <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Current Price</Typography>
                <Typography variant="h6">{formatCurrency(selectedPosition.current_price)}</Typography>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Market Value</Typography>
                <Typography variant="h6">{formatCurrency(selectedPosition.market_value)}</Typography>
                
                <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Unrealized P&L</Typography>
                <Typography 
                  variant="h6" 
                  sx={{ color: getPerformanceColor(selectedPosition.unrealized_pnl || 0) }}
                >
                  {formatCurrency(selectedPosition.unrealized_pnl || 0)}
                </Typography>
                
                <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>Total Return</Typography>
                <Typography 
                  variant="h6"
                  sx={{ color: getPerformanceColor(selectedPosition.total_return || 0) }}
                >
                  {formatPercentage(selectedPosition.total_return || 0)}
                </Typography>
              </Grid>
              
              {selectedPosition.sector && (
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" color="text.secondary">Sector</Typography>
                  <Chip label={selectedPosition.sector} variant="outlined" />
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default Portfolio;