# Unused Secrets Analysis

The following secrets/variables appear in configuration files but are not actively used in the deployment pipeline.

## `.env.example` vs Deployment
| Variable | Description | Recommendation |
|----------|-------------|----------------|
| `API_SECRET_KEY` | Likely legacy auth key | Remove from `.env.example` if replaced by Dhan/Google Auth |
| `JWT_SECRET` | Legacy JWT signing key | Remove if using ID tokens or other auth |
| `DATABASE_URL` | Local SQLite path | Clarify if Cloud SQL is needed for production |

## GCP Secret Manager
*   No unused GCP secrets found. All existing secrets (`dhan-*`) are mapped to services.
