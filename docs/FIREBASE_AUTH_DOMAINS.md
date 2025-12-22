# Firebase Authentication Domain Configuration

## Issue: `auth/unauthorized-domain` Error

When users try to sign in with Google, they see the error:
```
Firebase: Error (auth/unauthorized-domain)
```

This happens because the domain hosting the app is not in Firebase's list of authorized domains for OAuth redirects.

## Fix: Add Authorized Domains in Firebase Console

### Step 1: Open Firebase Console
Go to: https://console.firebase.google.com/project/gen-lang-client-0779271931/authentication/settings

### Step 2: Navigate to Authorized Domains
1. Click on **Authentication** in the left sidebar
2. Click on **Settings** tab
3. Scroll down to **Authorized domains** section

### Step 3: Add Required Domains
Add the following domains (click "Add domain" for each):

| Domain | Purpose |
|--------|---------|
| `localhost` | Local development |
| `gen-lang-client-0779271931.web.app` | Firebase Hosting default domain |
| `gen-lang-client-0779271931.firebaseapp.com` | Firebase alternative domain |
| `infinityai.pro` | Custom production domain |
| `www.infinityai.pro` | WWW subdomain |
| `dashboard.infinityai.pro` | Dashboard subdomain (if used) |

### Step 4: Save Changes
Click **Save** after adding all domains.

## Verification

After adding the domains:

1. Clear browser cache and cookies
2. Try signing in again with Google
3. The sign-in should now work without the `auth/unauthorized-domain` error

## Also Update Google Cloud Console OAuth

If you're using a custom domain, you also need to update OAuth consent screen:

1. Go to: https://console.cloud.google.com/apis/credentials/oauthclient
2. Select your OAuth 2.0 Client
3. Under **Authorized redirect URIs**, add:
   - `https://gen-lang-client-0779271931.firebaseapp.com/__/auth/handler`
   - `https://infinityai.pro/__/auth/handler`
4. Under **Authorized JavaScript origins**, add:
   - `https://infinityai.pro`
   - `https://gen-lang-client-0779271931.web.app`
   - `http://localhost:3000` (for development)

## Current Firebase Configuration

The app's Firebase config in `frontend/web-app/src/lib/firebase.ts`:

```typescript
const firebaseConfig = {
  apiKey: "<YOUR_FIREBASE_API_KEY_HERE>",
  authDomain: "gen-lang-client-0779271931.firebaseapp.com",
  projectId: "gen-lang-client-0779271931",
  storageBucket: "gen-lang-client-0779271931.appspot.com",
  messagingSenderId: "429140669077",
  appId: "<YOUR_FIREBASE_APP_ID_HERE>"
};
```

The `authDomain` determines where Firebase Auth redirects for OAuth. Make sure this domain is in your authorized domains list.

## Troubleshooting

### Still getting the error?
1. Check browser console for the exact error message
2. Verify the domain in the URL bar matches one in your authorized list
3. Clear browser cache completely
4. Try in an incognito window

### OAuth popup blocked?
1. Enable popups for your domain
2. Or use redirect-based auth instead of popup

### Custom domain not working?
1. Ensure DNS is properly configured
2. Verify SSL certificate is valid
3. Check Firebase Hosting is serving on that domain
