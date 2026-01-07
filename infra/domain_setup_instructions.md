# InfinityAI.Pro - Domain & API Key Setup Guide

## ❌ Current Status: FAILED

1.  **DNS Mismatch**: Your domain `infinityai.pro` points to `199.36.158.100` (Namecheap Parking), **NOT** Firebase Hosting.
2.  **API Key Restriction**: The error `auth/api-key-not-valid` confirms that `infinityai.pro` is not whitelisted in your Google Cloud API Credentials.

---

## ✅ Step 1: Fix DNS Records (Namecheap)

Go to Namecheap Dashboard -> Manage `infinityai.pro` -> **Advanced DNS**.

### 1. Delete Existing Records

Delete any **A Records** pointing to `199.36.158.100`.

### 2. Add Firebase Hosting A Records

Add the following two **A Records**:
| Type | Host | Value |
| :--- | :--- | :--- |
| **A** | `@` | `151.101.1.195` |
| **A** | `@` | `151.101.65.195` |

### 3. Add Custom Domain CNAME (App/Dashboard)

If you want `app.infinityai.pro` or `www.infinityai.pro` to work:
| Type | Host | Value |
| :--- | :--- | :--- |
| **CNAME** | `www` | `galvanic-pulsar-482815-h0.web.app.` |
| **CNAME** | `app` | `galvanic-pulsar-482815-h0.web.app.` |

> **Note**: DNS propagation can take 5 minutes to 24 hours.

---

## ✅ Step 2: Whitelist Domain in GCP (CRITICAL)

Your API Key (`AIzaSyD...`) is restricted to specific domains. You must add `infinityai.pro`.

1.  Go to **[Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)**.
2.  Project: **I Am Infinity** (`galvanic-pulsar-482815-h0`).
3.  Find the **Browser Key** (or the key starting with `AIzaSyD...`).
4.  Click **Edit** (Pencil Icon).
5.  Scroll to **Website restrictions** (Application restrictions).
6.  Click **Add Item** and enter:
    - `infinityai.pro`
    - `*.infinityai.pro`
    - `galvanic-pulsar-482815-h0.web.app` (Should already be there)
7.  Click **Save**.

---

## ✅ Step 3: Verify

1.  Wait 5-10 minutes.
2.  Visit `https://infinityai.pro`.
3.  The `auth/api-key-not-valid` error will disappear once Step 2 is done.
4.  The site will load correctly once Step 1 propagates.
