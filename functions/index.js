
const functions = require("firebase-functions");
const admin = require("firebase-admin");

admin.initializeApp();

/**
 * Updates the health status of an engine in Firestore.
 *
 * @param {Object} req The request object.
 * @param {Object} res The response object.
 */
exports.updateEngineHealth = functions.https.onRequest(async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).send("Method Not Allowed");
    return;
  }

  const { engineId, status } = req.body;

  if (!engineId || !status) {
    res.status(400).send("Missing required fields: engineId and status");
    return;
  }

  try {
    await admin.firestore().collection("engine_health").doc(engineId).set({
      status: status,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
    });
    res.status(200).send(`Successfully updated health for ${engineId}`);
  } catch (error) {
    console.error("Error updating engine health:", error);
    res.status(500).send("Internal Server Error");
  }
});

/**
 * Logs an AI signal to Firestore.
 *
 * @param {Object} req The request object.
 * @param {Object} res The response object.
 */
exports.logAISignal = functions.https.onRequest(async (.req, res) => {
  if (req.method !== "POST") {
    res.status(405).send("Method Not Allowed");
    return;
  }

  const { symbol, action, confidence, price } = req.body;

  if (!symbol || !action || !confidence || !price) {
    res.status(400).send("Missing required fields: symbol, action, confidence, and price");
    return;
  }

  try {
    await admin.firestore().collection("signals").add({
      symbol: symbol,
      action: action,
      confidence: confidence,
      price: price,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
    });
    res.status(200).send(`Successfully logged AI signal for ${symbol}`);
  } catch (error) {
    console.error("Error logging AI signal:", error);
    res.status(500).send("Internal Server Error");
  }
});

/**
 * Logs a trade to Firestore.
 *
 * @param {Object} req The request object.
 * @param {Object} res The response object.
 */
exports.logTrade = functions.https.onRequest(async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).send("Method Not Allowed");
    return;
  }

  const { symbol, action, quantity, price } = req.body;

  if (!symbol || !action || !quantity || !price) {
    res.status(400).send("Missing required fields: symbol, action, quantity, and price");
    return;
  }

  try {
    await admin.firestore().collection("trades").add({
      symbol: symbol,
      action: action,
      quantity: quantity,
      price: price,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
    });
    res.status(200).send(`Successfully logged trade for ${symbol}`);
  } catch (error) {
    console.error("Error logging trade:", error);
    res.status(500).send("Internal Server Error");
  }
});
