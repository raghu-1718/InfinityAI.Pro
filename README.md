# InfinityAI.Pro - Institutional Algorithmic Trading Platform

<div align="center">

![InfinityAI.Pro](https://img.shields.io/badge/InfinityAI.Pro-Institutional-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/version-4.1-green?style=for-the-badge)
![Status](https://img.shields.io/badge/status-Production-brightgreen?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-purple?style=for-the-badge)

**🚀 Next-Generation AI Trading Infrastructure for Indian Markets**

[Live Platform](https://infinityai.pro) | [Documentation](./docs/) | [Architecture](./docs/ARCHITECTURE.md)

</div>

---

## 🎯 Executive Summary

InfinityAI.Pro is a production-grade algorithmic trading platform engineered for high-frequency precision in Indian financial markets (NSE, BSE, NFO, MCX). Built on a distributed microservices architecture, it leverages **Google's Gemini 2.0 Flash** for real-time market reasoning and an **Ensemble ML Stack** (XGBoost, LightGBM, CatBoost) for predictive alpha generation.

The platform is designed with a **"Security-First, Zero-Trust"** philosophy, ensuring all trading logic is executed by a centralized, autonomous backend authority (Engine A) while the frontend serves as a strictly read-only control surface.

---

## 🌟 Key Features

### 🖥️ "Cyberpunk Institutional" UI (v4.1)
*   **Sweet, Attractive, Simple**: A completely redesigned interface focusing on clarity and rapid decision-making. No clutter, just critical data.
*   **Control Room**: Single-point "Engine Start/Stop" and "Kill Switch" for immediate system override.
*   **Live Intelligence**: Real-time AI signal cards with confidence intervals and "Brain Reasoning" transparency.
*   **Global Status Banner**: Instant visibility into system health and trading modes.

### 🔐 Enterprise Access Control (Family Plan)
*   **Secure binding**: 1:1 binding between Coupon Codes and Google User IDs.
*   **Family Plan**: Exclusive support for limited high-trust users with 10-year validity.
*   **Audit Trail**: Complete transparency on who accessed the system and when.

### 🧠 Autonomous AI Core
*   **Engine A (The Brain)**: Central Orchestrator responsible for Risk Management (VaR, CVaR, Kelly Criterion) and final trading decisions.
*   **Engine B (The Analyst)**: Dedicated AI cluster running Gemini 2.0 Flash and ML models to generate high-confidence trading signals.
*   **Engine C (The Hand)**: Stateless execution worker that interfaces with Broker APIs (DhanHQ) via secure OAuth 2.0 flow.

---

## 🏗 Architecture

### Three-Engine Distributed Cluster (Unified us-central1)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INFINITYAI.PRO CLUSTER v4.0                             │
│                         Region: us-central1 (Unified)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐                │
│   │   ENGINE A     │◄──►│   ENGINE B     │    │   ENGINE C     │                │
│   │  (Orchestrator)│    │   (AI Analyst) │    │   (Executor)   │                │
│   │    Python      │    │    Python      │    │    Python      │                │
│   │    FastAPI     │    │    FastAPI     │    │    FastAPI     │                │
│   │   Risk Gate    │    │ Gemini 2.0     │    │   Dhan API     │                │
│   └─────────────┬──┘    └────────────────┘    └────────▲───────┘                │
│                 │                                      │                        │
│                 └───────────────COMMAND────────────────┘                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Infrastructure Specs
| Component | Technology | Version | Role |
|-----------|------------|---------|------|
| **Frontend** | Next.js 16 | v4.1 | UI/UX Control Surface |
| **Engine A** | Cloud Run | v3.8 | Orchestration & Risk |
| **Engine B** | Cloud Run | v4.0 | AI Signal Generation |
| **Engine C** | Cloud Run | v3.8 | Trade Execution |
| **Database** | Firestore | Native | Real-time State |
| **Auth** | Firebase Auth | v9 | Security & Access |
| **Secrets** | Secret Manager | - | Zero-Trust Storage |

---

## 🔐 Security & Governance

### Zero-Trust Credentials
*   **No Hardcoded Secrets**: All API keys, tokens, and credentials are stored exclusively in **GCP Secret Manager**.
*   **Per-User Isolation**: Each user's broker session is isolated and encrypted.
*   **OAuth 2.0**: Full implementation of secure OAuth flows for broker connection.

### Risk Management (Engine A)
*   **Kill Switch**: Immediate, rigorous system halt capability.
*   **Confidence Gates**: Trades are only executed if AI confidence > 75%.
*   **Capital Protection**: Automated position sizing based on available margin and volatility.

---

## 🚀 Deployment

### Prerequisites
*   Google Cloud Platform Project
*   Firebase CLI Tools
*   DhanHQ API Credentials

### Deploy Command
```bash
# Deploy entire stack (Frontend + Backend Functions)
firebase deploy
```

---

## 📁 Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── engine-a/     # Authority & Risk
│   ├── engine-b/     # AI & ML Core
│   ├── engine-c/     # Execution Interface
├── frontend/
│   └── web-app/      # Next.js Dashboard
├── ml/               # Machine Learning Training Scripts
├── docs/             # Technical Documentation
└── firebase.json     # infrastructure-as-Code
```

---

## 📜 License

Copyright © 2025 InfinityAI.Pro. All rights reserved.

<div align="center">

**Built with ❤️ for Indian Traders**

![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=flat&logo=firebase&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)

</div>