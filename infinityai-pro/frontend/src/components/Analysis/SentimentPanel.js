import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, Typography, LinearProgress, Grid, Box, Chip } from '@mui/material';

const SentimentBar = ({ label, value, color }) => (
  <Box sx={{ mb: 1 }}>
    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>{Math.round(value * 100)}%</Typography>
    </Box>
    <LinearProgress variant="determinate" value={value * 100} color={color} />
  </Box>
);

const SentimentPanel = ({ apiUrl }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sentiment, setSentiment] = useState({
    overall: 0.5,
    retail: 0.5,
    institutional: 0.5,
    news: 0.5,
    social: 0.5
  });

  const fetchSentiment = useCallback(async () => {
    setError('');
    setLoading(true);
    try {
      // Endpoint exposed by Engine B and proxied via D; fallback to B if needed
      const resp = await fetch(`${apiUrl}/sentiment`);
      if (resp.ok) {
        const data = await resp.json();
        setSentiment({
          overall: data.overall ?? 0.5,
          retail: data.retail ?? 0.5,
          institutional: data.institutional ?? 0.5,
          news: data.news ?? 0.5,
          social: data.social ?? 0.5,
        });
        setLoading(false);
        return;
      }
    } catch (_) {}
    try {
      const respB = await fetch(`https://infinityai-engine-b-573866363639.us-central1.run.app/sentiment`);
      if (respB.ok) {
        const data = await respB.json();
        setSentiment({
          overall: data.overall ?? 0.5,
          retail: data.retail ?? 0.5,
          institutional: data.institutional ?? 0.5,
          news: data.news ?? 0.5,
          social: data.social ?? 0.5,
        });
      } else {
        setError('Failed to load sentiment');
      }
    } catch (e) {
      setError('Failed to load sentiment');
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchSentiment();
    const id = setInterval(fetchSentiment, 60_000);
    return () => clearInterval(id);
  }, [fetchSentiment]);

  const labelFor = (v) => v > 0.6 ? 'Bullish' : v < 0.4 ? 'Bearish' : 'Neutral';
  const colorFor = (v) => v > 0.6 ? 'success' : v < 0.4 ? 'error' : 'warning';

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Market Sentiment</Typography>
          <Chip size="small" color={colorFor(sentiment.overall)} label={labelFor(sentiment.overall)} />
        </Box>
        {loading ? (
          <LinearProgress />
        ) : (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <SentimentBar label="Overall" value={sentiment.overall} color={colorFor(sentiment.overall)} />
            </Grid>
            <Grid item xs={12} md={6}>
              <SentimentBar label="Retail" value={sentiment.retail} color={colorFor(sentiment.retail)} />
            </Grid>
            <Grid item xs={12} md={6}>
              <SentimentBar label="Institutional" value={sentiment.institutional} color={colorFor(sentiment.institutional)} />
            </Grid>
            <Grid item xs={12} md={6}>
              <SentimentBar label="News" value={sentiment.news} color={colorFor(sentiment.news)} />
            </Grid>
            <Grid item xs={12} md={6}>
              <SentimentBar label="Social" value={sentiment.social} color={colorFor(sentiment.social)} />
            </Grid>
          </Grid>
        )}
        {error && (
          <Typography variant="caption" color="error.main">{error}</Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default SentimentPanel;
