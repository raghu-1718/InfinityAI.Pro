import React, { useState, useEffect } from 'react';
import { Grid, Card, CardContent, Typography, Box, Paper, CircularProgress, Alert } from '@mui/material';
import { ShowChart, BarChart, CandlestickChart, Public, Memory, Speed } from '@mui/icons-material';
import { getMarketData, getSystemHealth } from '../../services/ApiService';

const StatCard = ({ title, value, icon, color, change, status }) => (
    <Card sx={{ height: '100%' }}>
        <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>{title}</Typography>
                {icon}
            </Box>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', mt: 1 }}>
                {value}
            </Typography>
            {change && (
                <Typography sx={{ color: change > 0 ? 'success.main' : 'error.main' }}>
                    {change > 0 ? '▲' : '▼'} {change}%
                </Typography>
            )}
            {status && (
                 <Typography variant="body2" sx={{ color: status === 'Open' ? 'success.main' : 'error.main', fontWeight: 'bold' }}>
                    {status}
                </Typography>
            )}
        </CardContent>
    </Card>
);

const EngineStatus = ({ name, status, cloud }) => (
    <Paper variant="outlined" sx={{ p: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: status === 'healthy' ? 'success.main' : 'error.main' }} />
        <Typography variant="body2" sx={{ flexGrow: 1 }}>{name}</Typography>
        <img src={`/${cloud}.png`} alt={cloud} width="20" />
    </Paper>
);


const LiveDashboard = () => {
    const [marketData, setMarketData] = useState(null);
    const [systemHealth, setSystemHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        try {
            const [market, health] = await Promise.all([
                getMarketData(),
                getSystemHealth()
            ]);
            setMarketData(market);
            setSystemHealth(health);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    if (loading) return <CircularProgress />;
    if (error) return <Alert severity="error">{error}</Alert>;

    const nifty = marketData?.indian_markets?.indices.find(i => i.name === 'NIFTY 50');
    const sensex = marketData?.indian_markets?.indices.find(i => i.name === 'SENSEX');
    const usMarket = marketData?.us_markets?.indices[0];

    return (
        <Box>
            <Typography variant="h4" gutterBottom>Live Dashboard</Typography>
            <Grid container spacing={3}>
                {/* Market Cards */}
                <Grid item xs={12} md={4}>
                    <StatCard title="NIFTY 50" value={nifty?.price} change={nifty?.change_percentage} status={marketData?.indian_markets?.status} icon={<ShowChart color="primary" />} />
                </Grid>
                <Grid item xs={12} md={4}>
                    <StatCard title="SENSEX" value={sensex?.price} change={sensex?.change_percentage} status={marketData?.indian_markets?.status} icon={<BarChart color="secondary" />} />
                </Grid>
                <Grid item xs={12} md={4}>
                    <StatCard title={usMarket?.name} value={usMarket?.price} change={usMarket?.change_percentage} status={marketData?.us_markets?.status} icon={<CandlestickChart color="success" />} />
                </Grid>

                {/* System Health */}
                <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>System & Engine Health</Typography>
                        <Grid container spacing={2}>
                            {systemHealth?.components && Object.entries(systemHealth.components).map(([key, value]) => (
                                <Grid item xs={6} sm={4} md={2} key={key}>
                                    <EngineStatus name={value.name} status={value.status} cloud={value.cloud} />
                                </Grid>
                            ))}
                        </Grid>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default LiveDashboard;
