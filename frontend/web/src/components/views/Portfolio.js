import React, { useState } from 'react';
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
  Info,
  Close as CloseIcon
} from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { usePortfolioData, useMarketData } from '../../hooks/useEngineData';

const Portfolio = ({ apiUrl, userId }) => {
  console.log('📊 Portfolio component mounted with userId:', userId);
  
  // Use real-time portfolio data hook
  const portfolioData = usePortfolioData();
  const { data: marketData } = useMarketData('', 10000);
  
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  
  // Indian market positions from live Dhan data
  const positions = portfolioData.positions || [];
  
  // Helper function to identify Indian market instruments
  const getIndianMarketInfo = (tradingSymbol) => {
    const symbol = tradingSymbol?.toUpperCase() || '';
    
    if (symbol.includes('NIFTY') || symbol.includes('BANKNIFTY')) {
      return { market: 'NSE', category: 'Index', sector: 'Index' };
    } else if (symbol.includes('CRUDEOIL') || symbol.includes('NATURALGAS')) {
      return { market: 'MCX', category: 'Commodity', sector: 'Energy' };
    } else if (symbol.includes('GOLD') || symbol.includes('SILVER')) {
      return { market: 'MCX', category: 'Commodity', sector: 'Precious Metals' };
    } else if (['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'].some(stock => symbol.includes(stock))) {
      return { market: 'NSE', category: 'Equity', sector: 'Large Cap' };
    } else {
      return { market: 'NSE/BSE', category: 'Equity', sector: 'Equity' };
    }
  };
  
  // Transform Dhan API data to component format
  const indianPositions = positions.map(pos => {
    const marketInfo = getIndianMarketInfo(pos.tradingSymbol);
    const currentValue = pos.netQty * pos.buyAvg;
    
    return {
      symbol: pos.tradingSymbol,
      quantity: pos.netQty || 0,
      avg_cost: pos.buyAvg || 0,
      current_price: pos.buyAvg || 0, // In live system, would get current price
      market_value: currentValue,
      unrealized_pnl: pos.unrealizedProfit || 0,
      unrealized_pnl_daily: pos.unrealizedProfit || 0, // Simplified
      market: marketInfo.market,
      category: marketInfo.category,
      sector: marketInfo.sector,
      exchange: pos.exchangeSegment || 'NSE',
      multiplier: pos.multiplier || 1,
      percentage_of_portfolio: 0 // Will be calculated
    };
  });


  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
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

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  // Calculate portfolio metrics using Indian market data
  const calculatePortfolioMetrics = () => {
    if (!indianPositions.length) {
      return {
        totalValue: 0,
        totalCost: 0,
        totalPnL: 0,
        totalPnLPercent: 0,
        dailyPnL: 0,
        dailyPnLPercent: 0,
        positionCount: 0,
        marketBreakdown: { NSE: 0, BSE: 0, MCX: 0 }
      };
    }

    const totalValue = indianPositions.reduce((sum, pos) => sum + (pos.market_value || 0), 0);
    const totalCost = indianPositions.reduce((sum, pos) => sum + (pos.quantity * pos.avg_cost), 0);
    const totalPnL = indianPositions.reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0);
    const totalPnLPercent = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;
    const dailyPnL = indianPositions.reduce((sum, pos) => sum + (pos.unrealized_pnl_daily || 0), 0);
    const dailyPnLPercent = totalValue > 0 ? (dailyPnL / totalValue) * 100 : 0;
    
    // Calculate market breakdown
    const marketBreakdown = indianPositions.reduce((acc, pos) => {
      const market = pos.market === 'NSE/BSE' ? 'NSE' : pos.market;
      acc[market] = (acc[market] || 0) + 1;
      return acc;
    }, { NSE: 0, BSE: 0, MCX: 0 });

    return {
      totalValue,
      totalCost,
      totalPnL,
      totalPnLPercent,
      dailyPnL,
      dailyPnLPercent,
      positionCount: indianPositions.length,
      marketBreakdown
    };
  };

  const metrics = calculatePortfolioMetrics();

  // Refresh handler
  const handleRefresh = () => {
    console.log('⚡ Portfolio data refresh requested');
    if (portfolioData.refresh) {
      portfolioData.refresh();
    }
  };

  // Prepare data for charts - Indian market focus
  const prepareAllocationData = () => {
    return indianPositions.map(pos => ({
      name: pos.symbol,
      value: pos.market_value,
      market: pos.market,
      percentage: ((pos.market_value / (metrics.totalValue || 1)) * 100).toFixed(1)
    }));
  };

  const prepareMarketData = () => {
    const marketMap = {};
    indianPositions.forEach(pos => {
      const market = pos.market === 'NSE/BSE' ? 'NSE' : pos.market;
      if (marketMap[market]) {
        marketMap[market] += pos.market_value;
      } else {
        marketMap[market] = pos.market_value;
      }
    });
    
    return Object.keys(marketMap).map(market => ({
      name: market,
      value: marketMap[market],
      percentage: ((marketMap[market] / (metrics.totalValue || 1)) * 100).toFixed(1)
    }));
  };

  const prepareSectorData = () => {
    const sectorMap = {};
    indianPositions.forEach(pos => {
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
      percentage: ((sectorMap[sector] / (metrics.totalValue || 1)) * 100).toFixed(1)
    }));
  };

  const preparePerformanceData = () => {
    return indianPositions.map(pos => ({
      symbol: pos.symbol,
      dailyPnL: pos.unrealized_pnl_daily || 0,
      totalPnL: pos.unrealized_pnl || 0,
      market: pos.market,
      category: pos.category,
      dailyReturn: pos.market_value ? ((pos.unrealized_pnl_daily || 0) / pos.market_value * 100).toFixed(2) : '0.00'
    }));
  };

  // Show loading state from portfolio data hook
  if (portfolioData.loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
          Loading Portfolio Data...
        </Typography>
      </Box>
    );
  }

  // Show error state from portfolio data hook
  if (portfolioData.error) {
    return (
      <Alert severity="error" sx={{ m: 3 }}>
        Error loading portfolio: {portfolioData.error}
        <Button onClick={handleRefresh} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Portfolio Overview
          </Typography>
          {portfolioData.lastUpdated && (
            <Typography variant="caption" color="text.secondary">
              Last updated: {new Date(portfolioData.lastUpdated).toLocaleTimeString()}
            </Typography>
          )}
        </Box>
        <Box>
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={portfolioData.loading}>
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
                {formatCurrency(metrics.totalValue)}
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
                {formatCurrency(portfolioData.cash_balance || 0)}
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
                    color: getPerformanceColor(metrics.dailyPnL)
                  }}
                >
                  {formatCurrency(metrics.dailyPnL)}
                </Typography>
                {getPerformanceIcon(metrics.dailyPnL)}
              </Box>
              <Typography 
                variant="body2" 
                sx={{ color: getPerformanceColor(metrics.dailyPnLPercent) }}
              >
                {formatPercentage(metrics.dailyPnLPercent / 100)}
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
                    color: getPerformanceColor(metrics.totalPnL)
                  }}
                >
                  {formatCurrency(metrics.totalPnL)}
                </Typography>
                {getPerformanceIcon(metrics.totalPnL)}
              </Box>
              <Typography 
                variant="body2" 
                sx={{ color: getPerformanceColor(metrics.totalPnLPercent) }}
              >
                {formatPercentage(metrics.totalPnLPercent / 100)}
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