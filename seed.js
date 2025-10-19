
const { initializeApp } = require("firebase/app");
const { getFirestore, collection, addDoc } = require("firebase/firestore");

// Your Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU",
  authDomain: "infinity-ai-5ec7c.firebaseapp.com",
  projectId: "infinity-ai-5ec7c",
  storageBucket: "infinity-ai-5ec7c.appspot.com",
  messagingSenderId: "26140490557",
  appId: "1:26140490557:web:6d99cdd77d3f9408c26354",
  measurementId: "G-3GPS2VZQS9"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// Sample data
const engineHealthData = [
  { id: "engine-1", status: "online" },
  { id: "engine-2", status: "offline" },
  { id: "engine-3", status: "online" },
  { id: "engine-4", status: "online" },
];

const aiSignalsData = [
  { signal: "BUY", symbol: "BTC/USD", timestamp: new Date() },
  { signal: "SELL", symbol: "ETH/USD", timestamp: new Date() },
  { signal: "BUY", symbol: "ADA/USD", timestamp: new Date() },
];

const tradesData = [
  { symbol: "BTC/USD", action: "BUY", quantity: 0.05, price: 65000, timestamp: new Date() },
  { symbol: "ETH/USD", action: "SELL", quantity: 1, price: 3500, timestamp: new Date() },
  { symbol: "ADA/USD", action: "BUY", quantity: 1000, price: 0.45, timestamp: new Date() },
  { symbol: "SOL/USD", action: "BUY", quantity: 10, price: 150, timestamp: new Date() },
];

// Function to seed data
async function seedDatabase() {
  console.log("Seeding database...");

  try {
    // Seed engine_health
    for (const data of engineHealthData) {
      await addDoc(collection(db, "engine_health"), data);
    }
    console.log("Engine health data seeded.");

    // Seed ai_signals
    for (const data of aiSignalsData) {
      await addDoc(collection(db, "ai_signals"), data);
    }
    console.log("AI signals data seeded.");

    // Seed trades
    for (const data of tradesData) {
      await addDoc(collection(db, "trades"), data);
    }
    console.log("Trades data seeded.");

    console.log("Database seeding complete!");

  } catch (error) {
    console.error("Error seeding database: ", error);
  }
}

seedDatabase();

