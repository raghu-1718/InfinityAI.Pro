# Coupon Verification Fix Report - 2026-01-05

## Problem

User encountered `TypeError: Failed to fetch` during Step 2 (Access Code) of login.

## Root Cause Analysis

1.  **Frontend Config**: Used `NEXT_PUBLIC_ENGINE_C_URL` or fallback to relative `/api`. Since env vars were cleared, it used relative path.
2.  **Hosting Rewrite**: The `firebase.json` configuration ONLY rewrote `/api/dhan/**` to the backend. It missed `/api/auth/**`.
    - **Effect**: Requests to `/api/auth/coupon/verify` hit the catch-all `**` -> `index.html` rule. The backend never saw the request. The browser received HTML instead of JSON, or failed network check if rewrites behaved oddly.
3.  **Backend Implementation**: `Engine C` (`main.py`) **DID NOT HAVE** the `POST /api/auth/coupon/verify` endpoint implemented. It only had the `OPTIONS` handler.
    - **Effect**: Even if rewrites worked, the backend would return `405 Method Not Allowed` or `404 Not Found`.

## Fixes Applied

1.  **Infrastructure**: Updated `firebase.json` to rewrite `/api/auth/**` to `engine-c`.
2.  **Backend**: Implemented `POST /api/auth/coupon/verify` and `POST /api/auth/logout` in `backend/engine-c/src/main.py` using the robust `CouponAuthManager`.
3.  **Deployment**: Redeployed `Engine C` and `Firebase Hosting`.
4.  **Permissions**: Explicitly granted `roles/run.invoker` to `allUsers` for `Engine C` to allow public access to the verification endpoint.
5.  **CORS**: Added Global `CORSMiddleware` to `Engine C` to ensure `Access-Control-Allow-Origin` correctly echoes the request origin.
6.  **System Reset**:
    - **Refactor**: Updated `CouponAuthManager` to use **Plain Text IDs** (e.g., `INFINITYDAD`).
    - **Logic**: Enforced strict `max_uses=1` and optional email binding.
    - **Data**: Seeded new coupon list (`INFINITY1718`, `INFINITYDAD`, etc.).
7.  **Frontend Fix**:
    - **Targeting**: Updated `verifyCoupon` to use relative path `/api/auth/coupon/verify` instead of absolute `NEXT_PUBLIC_ENGINE_C_URL`.
    - **Effect**: Requests now pass through Firebase Hosting Rewrites, eliminating CORS issues by sharing the same origin.

## Verification Steps

1.  **Navigate** to `https://infinityai.pro/login`.
2.  **Sign In** with Google (Step 1).
3.  **Enter Access Code**: `INFAI-FAM-DAD`.
4.  **Click "Verify Access Code"**.
5.  **Success**: You will be redirected to the Dashboard.

6.  **Navigate** to `https://infinityai.pro/login`.
7.  **Sign In** with Google (Step 1).
8.  **Enter Access Code**: `INFAI-FAM-DAD` (or any valid family code).
9.  **Click "Verify Access Code"**.
10. **Expected**:
    - Loader spins briefly.
    - Success message "Welcome to InfinityAI.Pro!".
    - Redirection to Dashboard (`/`).

## Technical details

- New Endpoint: `POST https://infinityai.pro/api/auth/coupon/verify`
- Handler: `CouponAuthManager.validate_coupon`
- Storage: Firestore `coupons` collection.
