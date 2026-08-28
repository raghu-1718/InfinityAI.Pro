# Engine B — AI & Machine Learning Intelligence Core

<div align="center">

![Engine B](https://img.shields.io/badge/Engine--B-AI%20%26%20ML%20Intelligence-brightgreen?style=for-the-badge&logo=googlecloud)
![Runtime](https://img.shields.io/badge/Runtime-Python%203.11%20%2F%20FastAPI-blue?style=for-the-badge&logo=python)
![Cloud Run](https://img.shields.io/badge/Cloud%20Run-asia--south1%20(2Gi%20Memory)-orange?style=for-the-badge&logo=googlecloud)
![Identity](https://img.shields.io/badge/IAM-sa--engine--b-purple?style=for-the-badge)

</div>

---

## 🧠 1. Engine Role & Responsibilities

**Engine B** is the high-performance AI and Machine Learning core of **InfinityAI.Pro**. It executes multi-model probability inference, feature extraction, continuous model synchronization, and institutional market regime arbitration.

### Core Responsibilities:
1. **Three-Class Primary Inference ($P_{\text{SELL}}, P_{\text{HOLD}}, P_{\text{BUY}}$):**
   * Computes normalized probability triplets satisfying $\sum P = 1.0000$.
   * Utilizes **BigQuery ML Boosted Trees** (`ML.PREDICT` on `project-841b7f97-5ee3-4fbe-920.infinity_dataset.xgboost_live_model`) as the primary inference engine (latency: 52–67 ms per query job).
2. **Tri-Model MLOps Ensemble & Model Vault:**
   * Synchronizes with **48 production model artifacts** stored in Google Cloud Storage (`gs://infinity-ai-models-vault/`):
     * **CatBoost Models:** `.cbm` artifacts for non-linear categorical interactions.
     * **LightGBM Models:** `.pkl` gradient boosted trees for high-speed feature splits.
     * **XGBoost Models:** `.json` optimized trees for structural tabular data.
     * **Statistical Modules:** Kalman Filters, Hidden Markov Model (HMM) regime detectors, and ARIMA trend predictors.
3. **Dynamic ADX Trend Strength Gate & Chop Veto:**
   * Calculates 14-period Wilder's ADX from raw continuous candle streams.
   * Enforces the **Institutional Capital Preservation Invariant**:
     $$\text{If } \text{ADX} < 25.0 \implies \text{VETO ACTIVATED} \implies \text{Action: } \mathbf{HOLD}$$
     $$\text{If } \text{ADX} \ge 25.0 \implies \text{VETO RELEASED} \implies \text{Action: } \mathbf{BUY\_CALL} \text{ / } \mathbf{BUY\_PUT}$$
4. **Vertex AI & Natural Language Processing (NLP):**
   * Integrates NLTK VADER and Vertex AI Gemini models for real-time news sentiment and macroeconomic event mining.

---

## ⚙️ 2. Cloud Infrastructure & Service Specs

* **Deployment Target:** Google Cloud Run (`asia-south1`)
* **Service Account:** `sa-engine-b@project-841b7f97-5ee3-4fbe-920.iam.gserviceaccount.com`
* **CPU / Memory Allocation:** 2 vCPU / 2Gi RAM *(Mandatory for ML inference libraries)*
* **Database Access:** BigQuery `ML.PREDICT` and Cloud Firestore `signals` collection.
* **Live Service URL:** `https://engine-b-r2f5flt77q-el.a.run.app`

---

## 📡 3. Key Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health check and loaded model status. |
| `POST` | `/api/v1/predict` | Single-symbol multi-model alpha signal generation. |
| `POST` | `/api/v1/predict/batch` | Parallelized multi-symbol BQML batch inference across 5 major indices. |
| `POST` | `/api/v1/market/analyze-options`| Vertex AI options open interest and volatility surface intelligence. |
| `POST` | `/api/v1/models/sync` | Re-downloads latest model artifacts from `gs://infinity-ai-models-vault/`. |

---

<div align="center">
  <sub>InfinityAI.Pro Engine B — Institutional AI / ML Quantitative Engine.</sub>
</div>
