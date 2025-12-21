# Firebase Configuration Audit

## Mismatch Detected: Build vs Deploy Source
*   **CI/CD Build**: Builds functions in `frontend/web/functions`.
*   **Firebase Config**: `firebase.json` points to `"source": "functions"` (Root directory).
*   **Root `functions/`**: Contains only a basic `index.js`.
*   **Risk**: The sophisticated functions code in `frontend/web/functions` (analyzed in CI/CD) is **NOT** being deployed. Instead, the simpler root `functions/` code is likely being pushed, or the deploy is failing silently/confusingly.
*   **Recommendation**: Update `firebase.json` to point `"source": "frontend/web/functions"` OR ensure CI/CD moves artifacts to root `functions`.

## Hosting Config
*   Source: `frontend` (Root `frontend` dir or `frontend/web-app`?)
    *   `firebase.json` says `"public": "frontend"`.
    *   Repo has `frontend/` directory (check if it contains build output).
    *   CI/CD builds Next.js in `frontend/web-app`.
    *   **Mismatch**: `firebase.json` expects static files in `frontend`, but Next.js build typically goes to `.next` or needs `firebase-frameworks` integration.
    *   If using standard hosting, `next export` output usually goes to `out`.
    *   **Action**: Verify where `npm run build` in `frontend/web-app` puts the output, and ensure `firebase.json` points there.

## Ignored Files
*   `firebase.json` correctly ignores `node_modules` and `.git`.
