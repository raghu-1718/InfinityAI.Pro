
# Commands to update GitHub repository secrets
# Run these in your GitHub repository settings or via GitHub CLI

gh secret set GOOGLE_CLOUD_PROJECT --body "infinity-ai-5ec7c"
gh secret set GOOGLE_CLOUD_REGION --body "us-central1"
gh secret set ENGINE_A_URL --body "https://infinityai-engine-a-26140490557.us-central1.run.app"
gh secret set ENGINE_B_URL --body "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app"
gh secret set ENGINE_C_URL --body "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app"
gh secret set ENGINE_D_URL --body "https://infinityai-engine-d-26140490557.us-central1.run.app"
gh secret set FRONTEND_URL --body "https://infinityai-frontend-ckxt6xvshq-uc.a.run.app"

# Service account key (get from GCP)
# gh secret set GCP_SA_KEY --body "$(cat path/to/service-account-key.json)"
