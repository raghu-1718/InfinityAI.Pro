import React, { useState, useEffect } from 'react';
import { AppBar, Toolbar, Typography, Box, Chip, IconButton } from '@mui/material';
import { Notifications as NotificationsIcon, Dns as DnsIcon } from '@mui/icons-material';
import { getSystemHealth } from '../../services/ApiService';

const Header = () => {
    const [systemStatus, setSystemStatus] = useState({ status: 'loading', engines: {} });
    const [notifications, setNotifications] = useState([]);

    const checkStatus = async () => {
        try {
            const data = await getSystemHealth();
            setSystemStatus({ status: data.status, engines: data.components || {} });

            const engineCount = Object.keys(data.components || {}).length;
            const healthyCount = Object.values(data.components || {}).filter(e => e.status === 'healthy').length;

            if (healthyCount < engineCount) {
                setNotifications(prev => [...prev, {
                    id: Date.now(),
                    type: 'warning',
                    message: `${healthyCount}/${engineCount} engines are operational.`
                }]);
            }
        } catch (error) {
            setSystemStatus({ status: 'error', engines: {} });
            setNotifications(prev => [...prev, {
                id: Date.now(),
                type: 'error',
                message: 'System health check failed. The aggregator engine may be down.'
            }]);
        }
    };

    useEffect(() => {
        checkStatus();
        const intervalId = setInterval(checkStatus, 30000); // Check every 30 seconds
        return () => clearInterval(intervalId);
    }, []);

    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy': return 'success';
            case 'degraded': return 'warning';
            case 'error':
            case 'unhealthy': return 'error';
            default: return 'info';
        }
    };

    return (
        <AppBar position="static">
            <Toolbar>
                <DnsIcon sx={{ mr: 2, fontSize: '2rem' }} />
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    InfinityAI.Pro
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Chip
                        label={`System: ${systemStatus.status}`}
                        color={getStatusColor(systemStatus.status)}
                        size="small"
                        sx={{ fontWeight: 'bold' }}
                    />
                    <IconButton color="inherit">
                        <NotificationsIcon />
                    </IconButton>
                    <Typography variant="body2">Welcome, Trader</Typography>
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default Header;
