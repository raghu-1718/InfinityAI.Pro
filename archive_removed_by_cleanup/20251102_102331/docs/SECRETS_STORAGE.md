# Secrets Storage (GCP)

All sensitive credentials must be stored in Google Secret Manager. Example:

- Secret: dhan-access-token
- Secret: dhan-client-id
- Secret: dhan-api-key
- Secret: dhan-api-secret

Access from code (Python) should use `google.cloud.secretmanager` with a fallback to environment variables for local development.

Ensure `.env` and any `*_credentials*.json` files are not committed. See `.gitignore`.