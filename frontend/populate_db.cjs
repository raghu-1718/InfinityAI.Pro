
const admin = require('firebase-admin');

admin.initializeApp({
  projectId: 'infinity-ai-5ec7c'
});

const db = admin.firestore();

async function populateDatabase() {
  try {
    const aiSignalRef = await db.collection('ai_signals').add({
      signal: 'BUY',
      symbol: 'BTC/USD',
      timestamp: new Date()
    });
    console.log('Added sample AI signal with ID: ', aiSignalRef.id);

    await db.collection('engine_health').doc('primary-engine').set({
      status: 'online',
      timestamp: new Date()
    });
    console.log('Added sample engine health status.');

    const tradeRef = await db.collection('trades').add({
      symbol: 'ETH/USD',
      action: 'SELL',
      quantity: 1.5,
      price: 2800.75,
      timestamp: new Date()
    });
    console.log('Added sample trade with ID: ', tradeRef.id);

    console.log('Database population complete.');
    process.exit(0);
  } catch (error) {
    console.error('Error populating database:', error);
    process.exit(1);
  }
}

populateDatabase();
