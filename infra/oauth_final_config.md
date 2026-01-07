# Final OAuth Client Configuration

You are 95% there! The Redirect URIs look perfect.
**However**, you are missing the **JavaScript Origins**. Without these, the browser will block the popup.

## 1. Authorized JavaScript Origins (MISSING)

You must add **both** of your hosting domains here so the browser allows the request.

- `https://infinityai.pro`
- `https://galvanic-pulsar-482815-h0.web.app`
- (Keep `http://localhost` etc.)

## 2. Authorized Redirect URIs (VERIFIED)

Ensure these three are present (as you showed me):

- `https://infinityai.pro/__/auth/handler`
- `https://galvanic-pulsar-482815-h0.firebaseapp.com/__/auth/handler`
- `https://galvanic-pulsar-482815-h0.web.app/__/auth/handler`

## 3. How to Update

1.  Go back to **[Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)**.
2.  Edit **Web client**.
3.  Under **Authorized JavaScript origins**, click **Add URI** for the missing domains above.
4.  **Save**.

## 4. Final Test

1.  Wait 1-2 minutes.
2.  Open **Incognito Window**.
3.  Login at `https://infinityai.pro/login`.
