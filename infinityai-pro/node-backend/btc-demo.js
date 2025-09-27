#!/usr/bin/env node

/**
 * BTC Options Trading Demo Script
 * Demonstrates the risk-managed BTC options strategy
 */

const API_BASE = 'http://localhost:3001/api';
const API_KEY = process.env.BACKEND_API_KEY || 'demo-key';

// Demo BTC price
const BTC_PRICE = 4500000;

async function demoBTCSignalGeneration() {
  console.log('🚀 InfinityAI Pro BTC Options Trading Demo');
  console.log('=' .repeat(50));

  try {
    // 1. Get BTC trading status
    console.log('\n📊 Getting BTC trading status...');
    const statusResponse = await fetch(`${API_BASE}/btc/status`, {
      headers: { 'x-api-key': API_KEY }
    });
    const status = await statusResponse.json();
    console.log('✅ Status:', status.configuration);

    // 2. Generate AI trading signal
    console.log('\n🎯 Generating AI trading signal...');
    const signalResponse = await fetch(`${API_BASE}/btc/signal`, {
      method: 'POST',
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ btcPrice: BTC_PRICE })
    });
    const signalData = await signalResponse.json();
    const signal = signalData.signal;
    console.log('✅ Signal generated:');
    console.log(`   Direction: ${signal.direction.toUpperCase()}`);
    console.log(`   Confidence: ${(signal.confidence * 100).toFixed(1)}%`);
    console.log(`   Reasoning: ${signal.reasoning}`);

    // 3. Check if trade should be executed
    if (signal.confidence >= 0.7) {
      console.log('\n💰 Executing BTC spread trade...');
      const tradeResponse = await fetch(`${API_BASE}/btc/trade`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          btcPrice: BTC_PRICE,
          direction: signal.direction,
          confidence: signal.confidence
        })
      });
      const tradeData = await tradeResponse.json();
      console.log('✅ Trade executed:');
      console.log(`   Type: ${tradeData.position.type}`);
      console.log(`   Buy Strike: ₹${tradeData.position.buyStrike.toLocaleString()}`);
      console.log(`   Sell Strike: ₹${tradeData.position.sellStrike.toLocaleString()}`);
      console.log(`   Premium: ₹${tradeData.position.premium.toLocaleString()}`);
      console.log(`   Max Loss: ₹${tradeData.position.maxLoss.toLocaleString()}`);
      console.log(`   Max Profit: ₹${tradeData.position.maxProfit.toLocaleString()}`);
    } else {
      console.log('\n⚠️  Signal confidence too low, skipping trade execution');
    }

    // 4. Get current positions
    console.log('\n📈 Getting current positions...');
    const positionsResponse = await fetch(`${API_BASE}/btc/positions`, {
      headers: { 'x-api-key': API_KEY }
    });
    const positionsData = await positionsResponse.json();
    console.log(`✅ Active positions: ${positionsData.activeCount}/${positionsData.count}`);

    // 5. Monitor positions
    console.log('\n👀 Monitoring positions...');
    const monitorResponse = await fetch(`${API_BASE}/btc/monitor`, {
      method: 'POST',
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ btcPrice: BTC_PRICE + 50000 }) // Simulate price movement
    });
    const monitorData = await monitorResponse.json();
    console.log('✅ Monitoring completed:');
    console.log(`   Current BTC Price: ₹${monitorData.currentBTCPrice.toLocaleString()}`);
    console.log(`   Positions monitored: ${monitorData.positionsMonitored}`);

    // 6. Get market data
    console.log('\n📊 Getting BTC market data...');
    const marketResponse = await fetch(`${API_BASE}/btc/market-data`, {
      headers: { 'x-api-key': API_KEY }
    });
    const marketData = await marketResponse.json();
    console.log('✅ Market data:');
    console.log(`   BTC Price: ₹${marketData.marketData.btcPrice.toLocaleString()}`);
    console.log(`   24h Change: ${marketData.marketData.change24h.toFixed(2)}%`);
    console.log(`   Volatility: ${marketData.marketData.volatility}`);

    console.log('\n🎉 BTC Options Trading Demo completed successfully!');
    console.log('\n💡 Key Features Demonstrated:');
    console.log('   ✅ AI-powered signal generation');
    console.log('   ✅ Risk-managed spread trading');
    console.log('   ✅ 5-8% max loss, 10-15% profit targets');
    console.log('   ✅ Real-time position monitoring');
    console.log('   ✅ ₹2,000-₹4,000 capital optimization');

  } catch (error) {
    console.error('❌ Demo failed:', error.message);
    console.log('\n🔧 Make sure the backend server is running:');
    console.log('   cd infinityai-pro/node-backend');
    console.log('   npm run dev');
  }
}

// Run the demo
if (require.main === module) {
  demoBTCSignalGeneration();
}

module.exports = { demoBTCSignalGeneration };