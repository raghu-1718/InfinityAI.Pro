# Dhan OAuth Settings for InfinityAI.Pro

Use the following in the Dhan developer portal for your application:

- Redirect URL: https://infinityai.pro/auth/dhan/callback
- Postback URL: https://infinityai.pro/api/webhooks/dhan

Notes
- These URLs are served via the production custom domain and reverse proxy.
- The postback is routed to Engine C securely under /api/webhooks/dhan.
- After you update keys, paste your fresh Access Token daily in the app under Broker Integration. It will be stored in Google Secret Manager.
- You can also retrieve these URLs in the UI: Broker Integration page shows both under the token update box.
