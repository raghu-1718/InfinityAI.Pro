# OAuth Redirect URI Fix

## ❌ The Problem

**Error**: `Error 400: redirect_uri_mismatch`
**Cause**: You verified the hosting domain (`infinityai.pro`), but the **Google OAuth Client** doesn't know about it yet.
Because we changed `authDomain` to `infinityai.pro`, Google Sign-In now redirects to:
`https://infinityai.pro/__/auth/handler`
This URL is **NOT** in your Authorized Redirect URIs list.

## ✅ The Fix (Manual Action Required)

1.  Go to **[Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)**.
2.  Select Project: **I Am Infinity** (`galvanic-pulsar-482815-h0`).
3.  Under **OAuth 2.0 Client IDs**, find the **Web client** (likely named "Web client (auto created by Google Service)").
4.  Click the **Pencil Icon** (Edit) to open details.
5.  Scroll down to **Authorized redirect URIs**.
6.  Click **Add URI** and enter EXACTLY:
    - `https://infinityai.pro/__/auth/handler`
7.  (Optional - Safety Net) Add these if missing:
    - `https://galvanic-pulsar-482815-h0.firebaseapp.com/__/auth/handler`
    - `https://galvanic-pulsar-482815-h0.web.app/__/auth/handler`
8.  Click **Save**.

## 🧪 Verification

1.  Wait 1-2 minutes for propagation.
2.  Open **Incognito Window**.
3.  Go to `https://infinityai.pro/login`.
4.  Click "Sign in with Google".
    - **Success**: You will see the Consent Screen ("Choose an account to continue to InfinityAI.Pro").
