# 🌐 Namecheap DNS Configuration for InfinityAI.Pro

## 📋 **DNS Records to Configure**

Once your engines are deployed to the cloud, configure these DNS records in your Namecheap account:

### **1. Main API (Engine D - Central Orchestrator)**
```
Type: CNAME
Host: api
Value: [AWS_LOAD_BALANCER_DNS_NAME]
TTL: 300 seconds (5 minutes)
```
**Example**: `api.infinityai.pro` → `infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com`

### **2. Engine A (Azure Sentiment & Technical Analysis)**
```
Type: CNAME  
Host: engine-a
Value: [AZURE_CONTAINER_INSTANCE_FQDN]
TTL: 300 seconds
```
**Example**: `engine-a.infinityai.pro` → `infinityai-engine-a.centralus.azurecontainer.io`

### **3. Engine B (Google Cloud Pattern Recognition)**
```
Type: CNAME
Host: engine-b  
Value: [GOOGLE_CLOUD_RUN_URL]
TTL: 300 seconds
```
**Example**: `engine-b.infinityai.pro` → `infinityai-engine-b-abc123-uc.a.run.app`

### **4. Engine C (AWS Quantitative Analysis)**
```
Type: CNAME
Host: engine-c
Value: [AWS_LOAD_BALANCER_DNS_NAME] 
TTL: 300 seconds
```
**Example**: `engine-c.infinityai.pro` → `infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com`

### **5. Frontend (Already Configured)**
```
Type: CNAME
Host: @  
Value: brave-ocean-09e85cd10-preview.centralus.2.azurestaticapps.net
TTL: 300 seconds

Type: CNAME
Host: www
Value: brave-ocean-09e85cd10-preview.centralus.2.azurestaticapps.net  
TTL: 300 seconds
```

---

## 🔧 **How to Configure in Namecheap**

### **Step 1: Access DNS Management**
1. Login to your Namecheap account
2. Go to "Domain List" 
3. Click "Manage" next to `infinityai.pro`
4. Go to the "Advanced DNS" tab

### **Step 2: Add Each CNAME Record**
1. Click "Add New Record"
2. Select "CNAME Record" from dropdown
3. Enter the Host and Value as specified above
4. Set TTL to 300 seconds
5. Click "Save All Changes"

### **Step 3: Verification**
After DNS propagation (5-10 minutes), verify each endpoint:

```bash
# Test main API
curl -I https://api.infinityai.pro/health

# Test Engine A  
curl -I https://engine-a.infinityai.pro/health

# Test Engine B
curl -I https://engine-b.infinityai.pro/health  

# Test Engine C
curl -I https://engine-c.infinityai.pro/health

# Test Frontend
curl -I https://infinityai.pro
curl -I https://www.infinityai.pro
```

---

## 🎯 **Expected Final Configuration**

| URL | Points To | Service |
|-----|-----------|---------|
| `https://infinityai.pro` | Azure Static Web Apps | **Frontend (React)** |
| `https://www.infinityai.pro` | Azure Static Web Apps | **Frontend (React)** |
| `https://api.infinityai.pro` | AWS Load Balancer | **Engine D (Central API)** |
| `https://engine-a.infinityai.pro` | Azure Container Instance | **Engine A (Sentiment/Technical)** |  
| `https://engine-b.infinityai.pro` | Google Cloud Run | **Engine B (ML/Patterns)** |
| `https://engine-c.infinityai.pro` | AWS Load Balancer | **Engine C (Quantitative)** |

---

## 🚀 **Complete System Architecture**

```
                    infinityai.pro (Frontend)
                            ↓
                   api.infinityai.pro
                      (Engine D - AWS)
                     /      |      \
                    /       |       \
         engine-a          engine-b        engine-c
        (Azure)            (GCP)           (AWS)
   Sentiment/Technical   ML/Patterns    Quantitative
```

---

## ⚡ **SSL/TLS Certificates**

All endpoints will automatically have SSL certificates:
- **Azure Static Web Apps**: Automatic SSL
- **AWS Load Balancer**: ACM Certificate  
- **Azure Container Instances**: Automatic HTTPS
- **Google Cloud Run**: Automatic SSL

---

## 🔍 **DNS Propagation Check**

Use these tools to verify DNS propagation:
- [DNS Checker](https://dnschecker.org)
- [What's My DNS](https://whatsmydns.net)  
- Command line: `nslookup api.infinityai.pro`

---

## 📞 **Support Contact**

If you encounter any DNS configuration issues:
1. Check Namecheap DNS management interface
2. Verify TTL settings (should be 300 seconds)
3. Wait for full DNS propagation (up to 24 hours globally)
4. Test from multiple locations/networks

**Your InfinityAI.Pro multi-cloud AI trading platform will be fully operational once these DNS records are configured!** 🚀