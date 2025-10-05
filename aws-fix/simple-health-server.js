// Simple health check server for Engine C and D
const express = require('express');
const app = express();

// Get port from environment or default
const PORT = process.env.PORT || 8000;
const ENGINE_TYPE = process.env.ENGINE_TYPE || 'unknown';

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    engine: ENGINE_TYPE,
    port: PORT,
    timestamp: new Date().toISOString()
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: `InfinityAI ${ENGINE_TYPE} Engine`,
    status: 'running',
    port: PORT
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`${ENGINE_TYPE} engine running on port ${PORT}`);
});

module.exports = app;