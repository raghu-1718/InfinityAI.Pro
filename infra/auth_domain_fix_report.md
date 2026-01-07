# Auth Domain Alignment Fix

## 1. The Issue

**Symptom**: "The requested action is invalid" during Google Sign-In.
**Cause**: The application was running on `infinityai.pro` but using `galvanic-pulsar...firebaseapp.com` as the Auth Domain. This cross-origin flow requires strict API Key whitelisting for _both_ domains. The `firebaseapp.com` domain was likely missing from your API Key restrictions, causing the handler to fail.

## 2. The Fix

I have updated the Frontend Configuration (`src/lib/firebase/config.ts`) to set **`authDomain: "infinityai.pro"`**.

**Why this works**:

1.  **Same Origin**: The Auth Handler now runs at `https://infinityai.pro/__/auth/handler`.
2.  **Whitelisted**: You confirmed `infinityai.pro` is in your API Key restrictions.
3.  **No redirects**: The popup/redirect stays on the verified domain, bypassing the `firebaseapp.com` restriction issue.

## 3. Verification

1.  **Close all tabs**.
2.  Open a **New Incognito Window**.
3.  Go to `https://infinityai.pro/login`.
4.  Click "Sign in with Google".
    - _Observation_: The popup URL should now start with `infinityai.pro`, NOT `firebaseapp.com`.
    - _Result_: You should be logged in successfully.

**Signed Off,**
_Antigravity SRE Team_
