# InfinityAI.Pro - Frontend Web App

100% Serverless Trading Dashboard built with Next.js, TailwindCSS, and React Query, deployed to **Firebase Hosting** and integrated with **Google Cloud Platform (Cloud Run & Firestore)**.

## Getting Started

First, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the dashboard.

## Production Build & Deployment

To build and deploy to Firebase Hosting:

```bash
npm run build
firebase deploy --only hosting
```

## Architecture
- **Hosting**: Firebase Hosting (`https://project-841b7f97-5ee3-4fbe-920.web.app`)
- **Backend Services**: Google Cloud Run (`asia-south1`)
  - Engine-A (Orchestration & Risk Management)
  - Engine-B (AI/ML Signal Generation)
  - Engine-C (DhanHQ Execution & Token Keep-Alive)
- **Database**: Google Cloud Firestore (Primary NoSQL Document Vault)
