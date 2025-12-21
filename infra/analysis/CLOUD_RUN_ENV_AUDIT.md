# Cloud Run Environment Audit

## Service: `engine-a`
*   **Env Vars**:
    *   `GOOGLE_CLOUD_PROJECT`: `gen-lang-client-0779271931`
    *   `ENGINE_B_URL`: `https://engine-b-...`
    *   `ENGINE_C_URL`: `https://engine-c-...`
*   **Secrets**:
    *   `DHAN_CLIENT_ID` -> `dhan-client-id:latest`
    *   `DHAN_API_SECRET` -> `dhan-api-secret:latest`
    *   `DHAN_ACCESS_TOKEN` -> `dhan-access-token:latest`

## Service: `engine-b`
*   **Env Vars**:
    *   `GOOGLE_CLOUD_PROJECT`: `gen-lang-client-0779271931`
    *   `ENGINE_A_URL`: `https://engine-a-...`
    *   `ENGINE_C_URL`: `https://engine-c-...`
*   **Secrets**:
    *   `DHAN_...` (All 3 mapped)
    *   `GEMINI_API_KEY` -> `gemini-api-key:latest` (**MISSING IN GCP**)

## Service: `engine-c`
*   **Env Vars**:
    *   `GOOGLE_CLOUD_PROJECT`: `gen-lang-client-0779271931`
    *   `ENGINE_A_URL`: `https://engine-a-...`
    *   `ENGINE_B_URL`: `https://engine-b-...`
*   **Secrets**:
    *   `DHAN_...` (All 3 mapped)
    *   `ENCRYPTION_KEY` -> `encryption-key:latest` (**MISSING IN GCP**)

## Connectivity Mesh
The services are correctly cross-referenced via URL env vars, creating a connected mesh (A <-> B <-> C).
