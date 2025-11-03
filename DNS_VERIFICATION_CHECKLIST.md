# DNS Update Verification Checklist

## Step 1: Verify in Namecheap Dashboard

1. Login: https://ap.www.namecheap.com/
2. Go to: **Domain List** → **infinityai.pro** → **Manage**
3. Click: **Advanced DNS** tab
4. Find the **A Record** entry:
   - **Type:** A Record
   - **Host:** @ (or blank)
   - **Value:** Should be `216.239.32.21` ✅
   - **TTL:** Automatic (or 5 min)

## Step 2: What You Should See

### ✅ CORRECT Configuration:
```
Type: A Record
Host: @
Value: 216.239.32.21  ← Must be this IP
TTL: Automatic
```

### ❌ INCORRECT (Old Vercel):
```
Type: A Record
Host: @
Value: 199.36.158.100  ← This is wrong
TTL: Automatic
```

## Step 3: If Value is Correct

DNS propagation is in progress. Wait 5-30 minutes and monitor:

```powershell
# Check every 2 minutes
while ($true) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    $ip = (nslookup infinityai.pro 8.8.8.8 | Select-String "Address:" | Select-Object -Last 1).ToString().Split(":")[-1].Trim()
    
    Write-Host "[$timestamp] infinityai.pro resolves to: $ip"
    
    if ($ip -eq "216.239.32.21") {
        Write-Host "✅ DNS UPDATED! Propagation complete." -ForegroundColor Green
        break
    }
    
    Start-Sleep -Seconds 120
}
```

## Step 4: If Value is Still Wrong

The update didn't save. Try again:

1. Click **Edit** on the A Record
2. Change Value to: `216.239.32.21`
3. Click **Save Changes** (green checkmark)
4. Wait for "Changes saved successfully" message
5. Refresh page and verify it shows `216.239.32.21`

## Common Issues

### Issue 1: Change Not Saving
- **Solution:** Clear browser cache, try different browser
- **Alternative:** Delete old A record, create new one with correct IP

### Issue 2: Multiple A Records
- **Problem:** Two A records for `@` host
- **Solution:** Delete the one with `199.36.158.100`, keep `216.239.32.21`

### Issue 3: Wrong TTL
- **Problem:** TTL set to 1 day (86400)
- **Solution:** Change TTL to "Automatic" or "5 min" for faster propagation

## Current Status Check

Run this to see current DNS status:

```powershell
# DNS Resolution Check
nslookup infinityai.pro 8.8.8.8

# Expected BEFORE update propagates:
# Address: 199.36.158.100

# Expected AFTER update propagates:
# Address: 216.239.32.21
```

## What's the Correct IP?

| Record Type | Host | Value | Purpose |
|-------------|------|-------|---------|
| **A** | `@` | `216.239.32.21` | Main domain → Firebase Hosting |
| CNAME | `www` | `ghs.googlehosted.com.` | www subdomain |
| CNAME | `engine-a` | `ghs.googlehosted.com.` | Engine A API |
| CNAME | `engine-b` | `ghs.googlehosted.com.` | Engine B API |
| CNAME | `engine-c` | `ghs.googlehosted.com.` | Engine C API |
| CNAME | `engine-d` | `ghs.googlehosted.com.` | Engine D API |

## Timeline

- **Immediate:** Update A record in Namecheap
- **0-5 min:** Update appears on Namecheap's DNS servers
- **5-30 min:** Global DNS propagation (caching clears)
- **15-60 min:** Google provisions SSL certificate
- **Total:** ~45-90 minutes until fully operational

---

**Please check your Namecheap dashboard and confirm the A record value!**
