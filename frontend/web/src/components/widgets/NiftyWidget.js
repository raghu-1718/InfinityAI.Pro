import React, { useEffect, useState, useCallback } from 'react';
import { API_CONFIG } from '../../config/api-config';
import { Card, CardContent, Box, Typography, Chip, LinearProgress } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';

const NiftyWidget = ({ apiUrl, symbol = 'NIFTY' }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [quote, setQuote] = useState(null);
  const [series, setSeries] = useState([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      // Try chart via Engine D first (proxied to A)
      let chartResp = await fetch(`${apiUrl}/chart/${symbol}?timeframe=1D`);
      if (chartResp.ok) {
        const data = await chartResp.json();
        const seriesData = (data.chart_data || []).map(d => ({ t: d.timestamp, v: d.close }));
        setSeries(seriesData);
        if (seriesData.length >= 2) {
          const last = seriesData[seriesData.length - 1].v;
          const first = seriesData[0].v;
          const change = last - first;
          const change_percent = first ? change / first : 0;
          setQuote({ last, change, change_percent });
        }
      } else {
        // Fallback to Engine A directly if proxy blocked by CORS
        try {
          const aBase = API_CONFIG.api.base_urls.engine_a;
          chartResp = await fetch(`${aBase}/chart/${symbol}?timeframe=1D`);
          if (chartResp.ok) {
            const data = await chartResp.json();
            const seriesData = (data.chart_data || []).map(d => ({ t: d.timestamp, v: d.close }));
            setSeries(seriesData);
            if (seriesData.length >= 2) {
              const last = seriesData[seriesData.length - 1].v;
              const first = seriesData[0].v;
              const change = last - first;
              const change_percent = first ? change / first : 0;
              setQuote({ last, change, change_percent });
            }
          }
        } catch (_) {}
      }
      // Optional: try quote; if available, it will refine the numbers
      try {
        const quoteResp = await fetch(`${apiUrl}/quote/${symbol}`);
        if (quoteResp.ok) setQuote(await quoteResp.json());
      } catch (_) {}
    } catch (e) {
      setError('Failed to load NIFTY data');
    } finally {
      setLoading(false);
    }
  }, [apiUrl, symbol]);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 30_000);
    return () => clearInterval(id);
  }, [fetchData]);

  const formatCurrency = (value) => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(value || 0);

  const change = quote?.change ?? 0;
  const changePct = quote?.change_percent ?? 0;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2" color="text.secondary">NSE</Typography>
          <Chip
            size="small"
            color={change >= 0 ? 'success' : 'error'}
            icon={change >= 0 ? <TrendingUp /> : <TrendingDown />}
            label={`${change >= 0 ? '+' : ''}${formatCurrency(change)} (${(changePct * 100).toFixed(2)}%)`}
          />
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
          {symbol} {quote ? formatCurrency(quote.last || quote.current_price) : ''}
        </Typography>
        {loading && <LinearProgress sx={{ mt: 1 }} />}
        {!loading && !error && (
          <Box sx={{ height: 80 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={series}>
                <XAxis dataKey="t" hide />
                <YAxis hide />
                <RechartsTooltip formatter={(v) => [formatCurrency(v), '']} labelFormatter={() => ''} />
                <Line type="monotone" dataKey="v" stroke={change >= 0 ? '#2e7d32' : '#d32f2f'} dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}
        {!loading && error && (
          <Typography variant="caption" color="error.main">{error}</Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default NiftyWidget;
