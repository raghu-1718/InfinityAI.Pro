import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  TextField,
  Autocomplete,
  Button,
  Tabs,
  Tab,
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  ShowChart,
  Timeline,
  Assessment,
  Insights,
  FilterList,
  Search
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  CandlestickChart,
  ReferenceLine
} from 'recharts';

const MarketAnalysis = ({ apiUrl }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedSymbol, setSelectedSymbol] = useState('SPY');
  const [timeframe, setTimeframe] = useState('1D');
  const [chartData, setChartData] = useState([]);
  const [marketData, setMarketData] = useState(null);
  const [topMovers, setTopMovers] = useState({ gainers: [], losers: [] });
  const [economicEvents, setEconomicEvents] = useState([]);
  const [sectorPerformance, setSectorPerformance] = useState([]);
  const [technicalIndicators, setTechnicalIndicators] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [symbolSuggestions, setSymbolSuggestions] = useState([]);

  // Popular symbols for analysis
  const popularSymbols = [
    'SPY', 'QQQ', 'IWM', 'VTI', 'DIA',
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META',
    'XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLP', 'XLU', 'XLRE',
    'GLD', 'SLV', 'TLT', 'UUP', 'VIX', 'USO'
  ];

  const timeframes = [
    { label: '1D', value: '1D' },
    { label: '5D', value: '5D' },
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '6M', value: '6M' },
    { label: '1Y', value: '1Y' },
    { label: '2Y', value: '2Y' },
    { label: '5Y', value: '5Y' }
  ];

  useEffect(() => {
    setSymbolSuggestions(popularSymbols);
    fetchMarketOverview();
    fetchTopMovers();
    fetchSectorPerformance();
    fetchEconomicEvents();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      fetchChartData();
      fetchTechnicalIndicators();
    }
  }, [selectedSymbol, timeframe]);

  const fetchChartData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl.replace('8003', '8001')}/chart/${selectedSymbol}?timeframe=${timeframe}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setChartData(data.chart_data || []);
        setMarketData(data.market_data);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
      setError('Failed to fetch chart data');
    } finally {
      setLoading(false);
    }
  };

  const fetchTechnicalIndicators = async () => {
    try {
      const response = await fetch(`${apiUrl.replace('8003', '8001')}/technical/${selectedSymbol}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setTechnicalIndicators(data.indicators || {});
      }
    } catch (error) {
      console.error('Error fetching technical indicators:', error);
    }
  };

  const fetchMarketOverview = async () => {
    try {
      const response = await fetch(`${apiUrl.replace('8003', '8001')}/market/overview`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setMarketData(data.market_data);
      }
    } catch (error) {
      console.error('Error fetching market overview:', error);
    }
  };

  const fetchTopMovers = async () => {
    try {
      const response = await fetch(`${apiUrl.replace('8003', '8001')}/market/movers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setTopMovers(data.movers || { gainers: [], losers: [] });
      }
    } catch (error) {
      console.error('Error fetching top movers:', error);
    }
  };

  const fetchSectorPerformance = async () => {
    try {
      const response = await fetch(`${apiUrl.replace('8003', '8001')}/market/sectors`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSectorPerformance(data.sectors || []);
      }
    } catch (error) {
      console.error('Error fetching sector performance:', error);
    }
  };

  const fetchEconomicEvents = async () => {
    try {
      const response = await fetch(`${apiUrl.replace('8003', '8001')}/economic/events`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setEconomicEvents(data.events || []);
      }
    } catch (error) {
      console.error('Error fetching economic events:', error);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getChangeColor = (value) => {
    return value >= 0 ? 'success.main' : 'error.main';
  };

  const getChangeIcon = (value) => {
    return value >= 0 ? <TrendingUp /> : <TrendingDown />;
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const handleSymbolSearch = (value) => {
    if (value.length >= 1) {
      const filtered = popularSymbols.filter(symbol => 
        symbol.toLowerCase().includes(value.toLowerCase())
      );
      setSymbolSuggestions(filtered);
    } else {
      setSymbolSuggestions(popularSymbols);
    }
  };

  // Custom candlestick chart component
  const CandlestickChart = ({ data }) => {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis domain={['dataMin - 5', 'dataMax + 5']} />
          <RechartsTooltip
            labelFormatter={(value) => new Date(value).toLocaleString()}
            formatter={(value, name) => [formatCurrency(value), name]}
          />
          <Line 
            type="monotone" 
            dataKey="close" 
            stroke="#8884d8" 
            strokeWidth={2}
            dot={false}
            name="Price"
          />
          {technicalIndicators.sma_20 && (
            <Line 
              type="monotone" 
              dataKey="sma_20" 
              stroke="#ff7300" 
              strokeWidth={1}
              dot={false}
              name="SMA 20"
            />
          )}
          {technicalIndicators.sma_50 && (
            <Line 
              type="monotone" 
              dataKey="sma_50" 
              stroke="#00ff00" 
              strokeWidth={1}
              dot={false}
              name="SMA 50"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          Market Analysis
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Autocomplete
            value={selectedSymbol}
            onChange={(event, newValue) => setSelectedSymbol(newValue)}
            onInputChange={(event, newInputValue) => handleSymbolSearch(newInputValue)}
            options={symbolSuggestions}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Symbol"
                variant="outlined"
                size="small"
                sx={{ width: 200 }}
              />
            )}
          />
          <FormControl size="small" sx={{ minWidth: 100 }}>
            <InputLabel>Timeframe</InputLabel>
            <Select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              label="Timeframe"
            >
              {timeframes.map((tf) => (
                <MenuItem key={tf.value} value={tf.value}>
                  {tf.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <IconButton onClick={() => {
            fetchChartData();
            fetchMarketOverview();
            fetchTopMovers();
            fetchSectorPerformance();
          }}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Chart Analysis" icon={<ShowChart />} />
        <Tab label="Market Overview" icon={<Assessment />} />
        <Tab label="Top Movers" icon={<Timeline />} />
        <Tab label="Economic Events" icon={<Insights />} />
      </Tabs>

      {/* Chart Analysis Tab */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    {selectedSymbol} Price Chart
                  </Typography>
                  {marketData && (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="h6" sx={{ mr: 1 }}>
                        {formatCurrency(marketData.current_price || 0)}
                      </Typography>
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          color: getChangeColor(marketData.change || 0),
                          display: 'flex',
                          alignItems: 'center'
                        }}
                      >
                        {getChangeIcon(marketData.change || 0)}
                        {marketData.change >= 0 ? '+' : ''}
                        {formatCurrency(marketData.change || 0)} ({formatPercentage(marketData.change_percent || 0)})
                      </Typography>
                    </Box>
                  )}
                </Box>
                
                {loading ? (
                  <LinearProgress />
                ) : (
                  <CandlestickChart data={chartData} />
                )}
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} lg={4}>
            {/* Technical Indicators */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Technical Indicators
                </Typography>
                
                <Grid container spacing={2}>
                  {technicalIndicators.rsi && (
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">RSI (14):</Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            fontWeight: 'bold',
                            color: technicalIndicators.rsi > 70 ? 'error.main' : 
                                   technicalIndicators.rsi < 30 ? 'success.main' : 'text.primary'
                          }}
                        >
                          {technicalIndicators.rsi.toFixed(2)}
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  
                  {technicalIndicators.macd && (
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">MACD:</Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            fontWeight: 'bold',
                            color: getChangeColor(technicalIndicators.macd)
                          }}
                        >
                          {technicalIndicators.macd.toFixed(4)}
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  
                  {technicalIndicators.bollinger_upper && (
                    <>
                      <Grid item xs={12}>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                          Bollinger Bands
                        </Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Upper:</Typography>
                          <Typography variant="body2">
                            {formatCurrency(technicalIndicators.bollinger_upper)}
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Middle:</Typography>
                          <Typography variant="body2">
                            {formatCurrency(technicalIndicators.bollinger_middle)}
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Lower:</Typography>
                          <Typography variant="body2">
                            {formatCurrency(technicalIndicators.bollinger_lower)}
                          </Typography>
                        </Box>
                      </Grid>
                    </>
                  )}
                </Grid>
              </CardContent>
            </Card>
            
            {/* Market Stats */}
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Market Statistics
                </Typography>
                
                {marketData && (
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Open:</Typography>
                        <Typography variant="body2">
                          {formatCurrency(marketData.open || 0)}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">High:</Typography>
                        <Typography variant="body2" sx={{ color: 'success.main' }}>
                          {formatCurrency(marketData.high || 0)}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Low:</Typography>
                        <Typography variant="body2" sx={{ color: 'error.main' }}>
                          {formatCurrency(marketData.low || 0)}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Volume:</Typography>
                        <Typography variant="body2">
                          {(marketData.volume || 0).toLocaleString()}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Market Cap:</Typography>
                        <Typography variant="body2">
                          {marketData.market_cap ? `$${(marketData.market_cap / 1e9).toFixed(2)}B` : 'N/A'}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">P/E Ratio:</Typography>
                        <Typography variant="body2">
                          {marketData.pe_ratio?.toFixed(2) || 'N/A'}
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Market Overview Tab */}
      {activeTab === 1 && (
        <Grid container spacing={3}>
          {/* Sector Performance */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Sector Performance
                </Typography>
                
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={sectorPerformance}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <RechartsTooltip formatter={(value) => [formatPercentage(value / 100), 'Performance']} />
                    <Bar 
                      dataKey="performance" 
                      fill={(entry) => entry.performance >= 0 ? '#4caf50' : '#f44336'}
                      name="Performance"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} lg={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Market Indices
                </Typography>
                
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Index</TableCell>
                      <TableCell align="right">Value</TableCell>
                      <TableCell align="right">Change</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {[
                      { symbol: 'SPY', name: 'S&P 500', value: 4150.25, change: 0.75 },
                      { symbol: 'QQQ', name: 'NASDAQ', value: 350.80, change: -0.45 },
                      { symbol: 'IWM', name: 'Russell 2000', value: 195.30, change: 1.20 },
                      { symbol: 'DIA', name: 'Dow Jones', value: 340.15, change: 0.30 }
                    ].map((index) => (
                      <TableRow key={index.symbol}>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {index.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {index.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatCurrency(index.value)}
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                            <Typography 
                              variant="body2" 
                              sx={{ color: getChangeColor(index.change) }}
                            >
                              {index.change >= 0 ? '+' : ''}{formatPercentage(index.change / 100)}
                            </Typography>
                            {getChangeIcon(index.change)}
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Top Movers Tab */}
      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, color: 'success.main' }}>
                  Top Gainers
                </Typography>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell align="right">Price</TableCell>
                        <TableCell align="right">Change</TableCell>
                        <TableCell align="right">Volume</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {topMovers.gainers.slice(0, 10).map((stock) => (
                        <TableRow key={stock.symbol} hover>
                          <TableCell>
                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                              {stock.symbol}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            {formatCurrency(stock.price)}
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                              <Typography variant="body2" sx={{ color: 'success.main' }}>
                                +{formatPercentage(stock.change_percent / 100)}
                              </Typography>
                              <TrendingUp color="success" sx={{ ml: 0.5 }} />
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            {stock.volume?.toLocaleString() || 'N/A'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, color: 'error.main' }}>
                  Top Losers
                </Typography>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell align="right">Price</TableCell>
                        <TableCell align="right">Change</TableCell>
                        <TableCell align="right">Volume</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {topMovers.losers.slice(0, 10).map((stock) => (
                        <TableRow key={stock.symbol} hover>
                          <TableCell>
                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                              {stock.symbol}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            {formatCurrency(stock.price)}
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                              <Typography variant="body2" sx={{ color: 'error.main' }}>
                                {formatPercentage(stock.change_percent / 100)}
                              </Typography>
                              <TrendingDown color="error" sx={{ ml: 0.5 }} />
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            {stock.volume?.toLocaleString() || 'N/A'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Economic Events Tab */}
      {activeTab === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Upcoming Economic Events
            </Typography>
            
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Event</TableCell>
                    <TableCell>Country</TableCell>
                    <TableCell align="center">Impact</TableCell>
                    <TableCell align="right">Forecast</TableCell>
                    <TableCell align="right">Previous</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {economicEvents.map((event, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(event.date).toLocaleDateString()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(event.date).toLocaleTimeString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="subtitle2">
                          {event.title}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={event.country} 
                          size="small" 
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={event.impact} 
                          color={getSeverityColor(event.impact)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        {event.forecast || 'N/A'}
                      </TableCell>
                      <TableCell align="right">
                        {event.previous || 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {economicEvents.length === 0 && (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography color="text.secondary">
                    No economic events available
                  </Typography>
                </Box>
              )}
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default MarketAnalysis;