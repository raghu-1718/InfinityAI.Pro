# LIVE VERIFICATION MISSION: READ-ONLY (PHASE 2)
**Project**: InfinityAI.Pro
**Mode**: 🔒 READ-ONLY (NO EXECUTION)
**Objective**: Prove end-to-end wiring, broker auth, and data flow without capital risk.

## 1. Broker Authentication & Demat Proof
- [ ] **Identity Check**: Verify Client ID & Status.
- [ ] **Funds Check**: Verify Available Balance & Margin.
- [ ] **Holdings**: Verify Holdings Fetch (Should function even if empty).
- [ ] **Positions**: Verify Positions Fetch.
- *Method*: Invoke `getdhanoverview` Cloud Function.

## 2. Live Market Data Verification (MCX)
- [ ] **Crude Oil Live Check**: Fetch LTP, Bid/Ask.
- [ ] **Historical Data**: Fetch recent candles.
- *Method*: Invoke Engine B Market Data endpoints for MCX.

## 3. AI/ML Inference on Live Data
- [ ] **Feed**: Inject Real MCX Data into Engine B.
- [ ] **Observe**: Signal Generation & Confidence Scores.
- [ ] **Verify**: Engine A receives signal but takes NO ACTION (due to market hours/config).

## 4. Firestore & Frontend Reflection
- [ ] **Persistence**: Check `activity_logs` for "Data Fetch" events.
- [ ] **State**: Check `users/{uid}/portfolio` updates in Firestore.

## 5. Security & Safety Check
- [ ] **Confirm**: No calls made to `place_order`.
- [ ] **Confirm**: No mutations on Broker side.

## Execution Plan
1.  **Auth & Portfolio**: Trigger `getdhanoverview`.
2.  **Market Data**: Trigger `getaisignals` (forces data fetch).
3.  **Audit**: Read Firestore & Logs.
