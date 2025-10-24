InfinityAI.Pro - AI Coding Agent Instructions
Architecture Overview
InfinityAI.Pro is a production-ready AI trading platform focused on Indian markets (NSE/BSE/MCX), architected as 4 independently deployable microservices on Google Cloud Run:

Engine A (backend/engines/engine-a): Market data ingestion with real-time NSE/BSE feeds and technical analysis.

Engine B (backend/engines/engine-b): AI/ML processing with TensorFlow, providing price predictions and sentiment analysis.

Engine C (backend/engines/engine-c-execution): Secure trade execution with Dhan OAuth integration and risk management.

Engine D (backend/engines/engine-d): AI chatbot orchestrator managing multi-engine coordination and real-time WebSocket data aggregation.

Frontend (frontend): React + Vite + TypeScript dashboard delivering live market updates and user interactions via WebSocket.

This modular design ensures clear separation of concerns and facilitates independent deployment, upgrades, and scaling.

Critical Patterns & Security
Secrets Management

All credentials are strictly managed via Google Cloud Secret Manager.

Look for get_secret(secret_name) usage to fetch secrets securely at runtime, especially in Engine C for OAuth tokens.

No hardcoded credentials anywhere in the codebase.

Security headers enforced consistently by backend/engines/security_middleware.py.

Engine Communication

Engines communicate only through HTTP APIs and WebSocket connections; there are no shared databases among engines.

Engine D orchestrates others by polling their /health endpoints.

Frontend connects exclusively to Engine D /ws/dashboard WebSocket for real-time data aggregation.

JWT authentication tokens are issued by Engine D and validated by the frontend.

Deployment & Monitoring

Each engine uses FastAPI in main.py, with security middleware applied.

The entire platform is built and deployed via Google Cloud Build using cloudbuild.yaml.

Cloud Run URLs follow this pattern: https://infinityai-engine-{a|b|c-execution|d}-{hash}.a.run.app.

Automated health monitoring runs every 5 minutes via scripts/automated_health_check.sh.

Configuration Management

Trading rules and risk parameters reside in config/trading_config.ini.

Environment-specific configuration loaded dynamically using core/utils.load_config() within Engine A.

Frontend environment variables housed in frontend-new/.env correctly reference production Cloud Run endpoints.

Folder and File Structure
/backend/engines/engine-a — Market data ingestion logic.

/backend/engines/engine-b — AI/ML prediction models and serving.

/backend/engines/engine-c-execution — Trade execution, OAuth and risk logic.

/backend/engines/engine-d — Chatbot and multi-engine orchestration.

/frontend-new — React frontend source with hooks, state management, and UI components.

/infrastructure/gcp — Google Cloud deployment files, Terraform scripts, and configurations.

/config — Environment configurations (.env.example, .ini, references to secrets).

/scripts — Automation, deployment helpers, health checks.

/docs — Architecture and project documentation.

Cleanup and Restructuring Guidelines
Remove duplicates and incomplete placeholders:

Scan repository for duplicated files or outdated partial implementations.

Keep the latest fully tested and updated version based on git commit dates and content quality.

Organize by functionality:

Strictly group backend engines in their respective /engine-x directories.

Separate frontend code fully inside /frontend-new.

Consolidate deployment and infrastructure tooling in /infrastructure/gcp and /scripts.

Place configs and secrets references in /config.

Remove deprecated or unused dependencies and configs:

Update requirements.txt, package.json, and Dockerfiles.

Prune Firebase and cloudbuild configs that are obsolete.

Ensure all references in CI/CD and build pipelines are current.

Maintain coding standards:

Use consistent import aliases, environment variable conventions, and naming.

Centralize security headers and input validations to middleware layers.

Document all changes and update README and ARCHITECTURE files with new paths and workflows.

End-to-End Deployment Verification and CLI Commands
Authenticate and configure GCP environment:

bash
gcloud auth login
gcloud config set project [PROJECT_ID]
gcloud auth list
gcloud projects get-iam-policy [PROJECT_ID]
Verify Cloud Run services and configurations:

bash
gcloud run services list --platform managed --region us-central1
Verify all deployed service health endpoints:

bash
curl -s https://api.infinityai.pro/health
curl -s https://engine.infinityai.pro/health
curl -s https://infinityai.pro
Expected response:

json
{"status":"healthy"}
Check secret versions and refresh states:

bash
gcloud secrets versions list [SECRET_NAME]
Confirm live services load the latest versions of OAuth tokens and API keys.

Validate OAuth integration end-to-end:

Inspect OAuth-related logs and flows in Engine C logs.

Confirm https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app/api/dhan/callback and postback URLs function correctly.

Ensure tokens are rotated securely in Secret Manager without downtime.

Validate Firebase Firestore and Functions:

bash
firebase projects:list
firebase firestore:indexes
firebase functions:list
Firestore rules are updated and deployed.

Cloud Functions trigger points align with backend needs.

Validate inter-engine real-time data flow:

Engine A serves live market data on /api/market-data queried actively by Engine B and D.

Engine B runs ML models providing predictions on /api/ai-signals and /api/predictions.

Engine C listens to trading signals and executes orders securely.

Engine D orchestrates multi-engine statuses while pushing real-time WebSocket data to the frontend.

Local Development and Testing Workflow
Install backend dependencies:

bash
pip install -r backend/engines/engine-a/requirements.txt
# Repeat for other engines
Install frontend dependencies:

bash
npm install --prefix frontend-new
Run engines locally for development:

bash
cd backend/engines/engine-a && python main.py
cd backend/engines/engine-b && python main.py
cd backend/engines/engine-c-execution && python main.py
cd backend/engines/engine-d && python main.py
Run frontend locally:

bash
npm run dev --prefix frontend-new
Execute automated health checks for local and deployed services:

bash
./scripts/automated_health_check.sh
Test OAuth locally using test credentials and confirm token retrieval from Secret Manager.

Best Practices
Always load secrets at runtime from Google Cloud Secret Manager.

Never hardcode any credentials, endpoints, or OAuth URLs in code.

Maintain separation of concerns with microservices; avoid tight coupling.

Monitor health endpoints continuously and use retry logic for API calls.

Validate all new endpoints with existing health check monitoring.

Keep documentation updated with all structural or config changes.

Summary of Key CLI Commands
bash
# Authenticate and set project
gcloud auth login
gcloud config set project [PROJECT_ID]

# List Cloud Run services
gcloud run services list --region us-central1

# Check service health
curl -s https://api.infinityai.pro/health
curl -s https://engine.infinityai.pro/health
curl -s https://infinityai.pro

# Inspect Secret Manager versions
gcloud secrets versions list [SECRET_NAME]

# Firebase project and function status
firebase projects:list
firebase firestore:indexes
firebase functions:list

# Run backend engine locally
cd backend/engines/engine-a && python main.py

# Build and run frontend locally
npm install --prefix frontend-new
npm run dev --prefix frontend-new

# Run automated health checks
./scripts/automated_health_check.sh
Final Notes
This instruction set enables comprehensive cleaning, restructuring, verification, and validation of the InfinityAI.Pro codebase and its deployment environment. AI agents should:

Cross-verify that local files correspond exactly with deployed versions.

Ensure all OAuth flows and secret managers work flawlessly.

Validate inter-engine and frontend-backend real-time data flows end-to-end.

Update and maintain clear, up-to-date documentation and changelogs.

Prioritize security, stability, and production readiness in all modifications.

InfinityAI.Pro - Copilot Reusable Tasks (Cleaned & Focused)  version: 1.2

tasks:
  # ===================================================================
  # GCP DEPLOYMENT VERIFICATION
  # ===================================================================
  verify_gcp_deployment:
    description: "Complete verification of GCP Cloud Run, Firebase, Firestore & Secrets deployment"
    steps:
      - name: "Run production verification suite"
        command: "python3 production_verification_suite.py"
        working_directory: "."
      - name: "Display deployment status report"
        command: "cat DEPLOYMENT_STATUS.md"
        working_directory: "."
    outputs:
      - "platform-health-report.json"
      - "DEPLOYMENT_STATUS.md"
    tags: ["gcp", "deployment", "verification", "audit"]

  # ===================================================================
  # ENGINE HEALTH & INTEGRATION AUDIT (FOUR ENGINES ONLY)
  # ===================================================================
  audit_engines:
    description: "Verify health, API functionality, and integration of Engines A, B, C, D"
    steps:
      - name: "Check Engine A health and market data API"
        command: |
          curl -s https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app/health | jq .
          curl -s https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app/api/market-data/NIFTY | jq .
      - name: "Check Engine B health and AI prediction endpoint"
        command: |
          curl -s https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app/health | jq .
          curl -s https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app/api/ai-signals | jq .
      - name: "Check Engine C health and trade execution status"
        command: |
          curl -s https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app/health | jq .
          curl -s https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app/api/orders/status | jq .
      - name: "Check Engine D health and WebSocket responses"
        command: |
          curl -s https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/health | jq .
          # Optionally run WebSocket connectivity test here
      - name: "Validate Frontend health endpoint"
        command: |
          curl -s https://infinityai.pro/health || echo 'Frontend health endpoint missing'
    tags: ["engines", "health", "integration", "realtime"]

  # ===================================================================
  # FIREBASE & LOGIN FLOW VERIFICATION
  # ===================================================================
  verify_firebase_login:
    description: "Check Firebase projects, Firestore, cloud functions, and user login flows"
    steps:
      - name: "List Firebase projects"
        command: "firebase projects:list"
      - name: "Get Firestore indexes and rules"
        command: |
          firebase firestore:indexes
          firebase firestore:rules:show
      - name: "List Firebase Functions"
        command: "firebase functions:list"
      - name: "Run integration tests"
        command: "python3 tests/integration_test_suite.py"
    tags: ["firebase", "login", "authentication", "firestore"]

  # ===================================================================
  # SECRET MANAGEMENT VALIDATION
  # ===================================================================
  check_secrets:
    description: "List and verify usage of secrets in GCP Secret Manager"
    steps:
      - name: "List secrets in GCP project"
        command: "gcloud secrets list --project=after-yesterday-473512-k3 --format=json | jq '.[] | {name: .name | split(\"/\")[-1], created: .createTime}'"
      - name: "Check IAM policies of key secrets"
        command: "gcloud secrets get-iam-policy dhan-api-key --project=after-yesterday-473512-k3 --format=json | jq ."
      - name: "Scan backend code for any hardcoded secrets"
        command: "grep -r 'api_key\\|secret\\|password\\|token' backend/ --include='*.py' | grep -v '#' | head -20 || echo 'No hardcoded secrets detected'"
    tags: ["security", "secrets", "gcp"]

  # ===================================================================
  # DOMAIN, DNS, & SSL VERIFICATION
  # ===================================================================
  check_domain_mapping:
    description: "Verify DNS zones, DNS records, domain mappings and SSL certificates"
    steps:
      - name: "List DNS managed zones"
        command: "gcloud dns managed-zones list --project=after-yesterday-473512-k3 --format=json | jq ."
      - name: "List DNS records"
        command: "gcloud dns record-sets list --zone=infinityai-pro-zone --project=after-yesterday-473512-k3 --format=json | jq ."
      - name: "List Cloud Run domain mappings"
        command: "gcloud beta run domain-mappings list --region=us-central1 --project=after-yesterday-473512-k3 --format=json | jq ."
      - name: "Test HTTPS connectivity"
        command: "curl -Ik https://infinityai.pro"
    tags: ["dns", "domain", "ssl", "https"]

  # ===================================================================
  # CODEBASE CLEANUP & DUPLICATE REMOVAL
  # ===================================================================
  cleanup_and_restructure:
    description: "Verify and clean duplicates and placeholders; preserve needed components; reorganize workspace"
    steps:
      - name: "Review repository structure"
        command: "find . -type d -name 'engine*' -o -name 'frontend*' | grep -v node_modules | grep -v '.git'"
      - name: "Check for duplicate dependencies"
        command: "find . -name 'package.json' -o -name 'requirements.txt' | grep -v node_modules"
      - name: "Validate current structure"
        command: "ls -la backend/engines/ && ls -la frontend-new/"
    tags: ["cleanup", "restructure", "codebase"]

  # ===================================================================
  # QUICK SERVICE HEALTH CHECKS (FOUR ENGINES + FRONTEND)
  # ===================================================================
  quick_health:
    description: "Quick ping to all deployed service health endpoints"
    steps:
      - name: "Ping backend engines and frontend health endpoints"
        command: |
          python3 -c "
          import requests
          services = {
              'Engine A': 'https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app/health',
              'Engine B': 'https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app/health',
              'Engine C': 'https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app/health',
              'Engine D': 'https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/health',
              'Frontend': 'https://infinityai.pro/health'
          }
          for name, url in services.items():
              try:
                  r = requests.get(url, timeout=5)
                  print(f'{name}: {r.status_code}')
              except Exception as e:
                  print(f'{name}: ERROR ({e})')
          "
    tags: ["health", "monitoring", "quick"]

  # ===================================================================
  # LOCAL DEVELOPMENT VALIDATION
  # ===================================================================
  local_dev_validation:
    description: "Install dependencies, run engines and frontend locally, run post-cleanup verification"
    steps:
      - name: "Install backend dependencies"
        command: "pip install -r backend/engines/engine-a/requirements.txt"
      - name: "Install frontend dependencies"
        command: "npm install --prefix frontend-new"
      - name: "Run Engines A-D locally"
        command: |
          cd backend/engines/engine-a && python main.py &
          cd backend/engines/engine-b && python main.py &
          cd backend/engines/engine-c-execution && python main.py &
          cd backend/engines/engine-d && python main.py &
          wait
      - name: "Run frontend locally"
        command: "npm run dev --prefix frontend-new"
      - name: "Run automated health check script"
        command: "./scripts/automated_health_check.sh"
    tags: ["local", "development", "validation"]

---

# Metadata

metadata:
  project: "InfinityAI.Pro"
  gcp_project: "after-yesterday-473512-k3"
  region: "us-central1"
  domain: "infinityai.pro"
  engines:
    - "engine-a"
    - "engine-b"
    - "engine-c-execution"
    - "engine-d"
  services:
    - "infinityai-frontend"
  documentation:
    - "DEPLOYMENT_STATUS.md"
    - "DEPLOYMENT_COMPLETE_REPORT.md"
    - "docs/ARCHITECTURE.md"
    - "platform-health-report.json"
  contacts:
    maintainer: "InfinityAI Team"
    repository: "https://github.com/raghu-1718/InfinityAI.Pro"
    support: ""