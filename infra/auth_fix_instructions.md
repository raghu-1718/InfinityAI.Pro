# Authorization Fix Instructions

## 1. Config Alignment (Completed)

I have updated your Frontend Code to match the **exact settings** you pasted from the Firebase Console (`AIzaSyD...`).
The frontend is re-deploying now.

## 2. Whitelist the Domain (REQUIRED)

The error `auth/unauthorized-domain` means Google does not trust your hosting URL yet.
You **MUST** do this manually in the Firebase Console:

1.  Go to **[Firebase Console](https://console.firebase.google.com/)**.
2.  Select Project: **I Am Infinity** (`galvanic-pulsar...`).
3.  Go to **Authentication** (left sidebar) -> **Settings** tab -> **Authorized Domains** tab.
4.  Click **Add Domain**.
5.  Add: `galvanic-pulsar-482815-h0.web.app`
6.  (Optional) Add: `galvanic-pulsar-482815-h0.firebaseapp.com` (should be there).

## 3. Verify

After adding the domain, refresh your app (`galvanic-pulsar-482815-h0.web.app/login`) and try "Sign in with Google" again.
It should work immediately.
