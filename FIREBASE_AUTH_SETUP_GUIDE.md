# Firebase Authentication Setup Guide

## 🚨 **ISSUE IDENTIFIED: Firebase Authentication Not Configured**

The error `auth/configuration-not-found` occurs because Firebase Authentication is not properly set up for the project `infinity-ai-5ec7c`.

## 🔧 **IMMEDIATE FIX REQUIRED**

### **Step 1: Enable Firebase Authentication**

1. **Go to Firebase Console**: 
   ```
   https://console.firebase.google.com/project/infinity-ai-5ec7c/authentication
   ```

2. **Click "Get Started" on Authentication**
   - If you see a "Get Started" button, click it to initialize Authentication
   - This will enable the Authentication service for your project

### **Step 2: Enable Email/Password Sign-in Method**

1. **Go to Sign-in Method tab**:
   ```
   https://console.firebase.google.com/project/infinity-ai-5ec7c/authentication/providers
   ```

2. **Enable Email/Password Provider**:
   - Click on "Email/Password" 
   - Toggle "Enable" to ON
   - Click "Save"

### **Step 3: Add Test User (Optional)**

1. **Go to Users tab**:
   ```
   https://console.firebase.google.com/project/infinity-ai-5ec7c/authentication/users
   ```

2. **Add User**:
   - Click "Add User"
   - Email: `raghu42620@gmail.com` (as shown in the login form)
   - Password: Set a test password
   - Click "Add User"

## 🎯 **VERIFICATION AFTER SETUP**

After completing the above steps, test the authentication:

### **Test 1: Check API Access**
```bash
curl -X POST "https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU" \
  -H "Content-Type: application/json" \
  -d '{"idToken": "test"}'
```

**Expected Result**: Should return a proper error (not configuration-not-found)

### **Test 2: Frontend Login**
1. Go to: https://infinity-ai-5ec7c.web.app/login
2. Try logging in with the credentials you set up
3. Should work without `auth/configuration-not-found` error

## 📋 **TECHNICAL DETAILS**

### **Current Firebase Configuration**
```typescript
// frontend/src/firebase.ts
const firebaseConfig = {
  projectId: "infinity-ai-5ec7c",
  appId: "1:26140490557:web:6d99cdd77d3f9408c26354", 
  apiKey: "AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU",
  authDomain: "infinity-ai-5ec7c.firebaseapp.com",
  // ... other config
};
```

### **Issue Analysis**
- ✅ Firebase project exists: `infinity-ai-5ec7c`
- ✅ API key is correct: `AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU`  
- ✅ Auth domain is correct: `infinity-ai-5ec7c.firebaseapp.com`
- ❌ **Authentication service not initialized**

### **API Endpoint Being Called**
```
POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU
```

## ⚡ **QUICK ACTIONS**

### **Option 1: Manual Setup (Recommended)**
Follow Steps 1-3 above in Firebase Console

### **Option 2: CLI Setup (If Available)**
```bash
# Note: This may not work without proper gcloud setup
firebase auth:import users.json --project infinity-ai-5ec7c
```

### **Option 3: Programmatic Setup**
```javascript
// Using Firebase Admin SDK (server-side only)
const admin = require('firebase-admin');
admin.auth().updateProjectConfig({
  signInOptions: {
    email: { enabled: true }
  }
});
```

## 🎉 **SUCCESS INDICATORS**

After proper setup, you should see:

1. **Firebase Console**: Authentication dashboard shows enabled providers
2. **Frontend**: Login works without configuration errors  
3. **API Calls**: Authentication endpoints respond correctly
4. **User Management**: Can create/manage users in Firebase Console

## 🔄 **NEXT STEPS AFTER SETUP**

1. **Test Login Flow**: Verify user can sign in successfully
2. **Test Function Calls**: Verify authenticated HTTP callable functions work
3. **Update Documentation**: Document the authentication setup for team
4. **Set Up Additional Providers**: Enable Google, GitHub, etc. if needed

---

**Priority**: 🚨 **CRITICAL** - Authentication must be configured for app to function  
**Time Required**: ~5 minutes manual setup  
**Impact**: Fixes all authentication-related errors in the application