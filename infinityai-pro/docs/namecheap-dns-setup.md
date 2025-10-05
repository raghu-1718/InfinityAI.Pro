# InfinityAI.Pro - Namecheap DNS Configuration Guide

Complete guide for configuring DNS records on Namecheap to connect your domain to the multi-cloud InfinityAI.Pro architecture.

## Overview

Your InfinityAI.Pro system uses a multi-cloud architecture:
- **Frontend (React)**: Azure App Service → `infinityai.pro`
- **Backend API (Engine D)**: AWS ECS + ALB → `api.infinityai.pro`
- **AI Gateway**: Vercel → `ai.infinityai.pro`

## Prerequisites

1. Domain: `infinityai.pro` registered on Namecheap
2. AWS Application Load Balancer deployed and running
3. Azure App Service deployed and running
4. Vercel AI Gateway deployed (optional)

## Step 1: Get Required IP Addresses and CNAMEs

### Azure App Service Details
After running the Azure deployment script, get the App Service IP:

```bash
# Get Azure App Service IP
az webapp show --name infinityai-pro --resource-group infinityai-rg --query "defaultHostName" -o tsv
# Result: infinityai-pro.azurewebsites.net

# Get the actual IP address
nslookup infinityai-pro.azurewebsites.net
```

### AWS Load Balancer Details
After running the AWS deployment script, get the ALB DNS name:

```bash
# Get Application Load Balancer DNS name
aws elbv2 describe-load-balancers --names infinityai-engine-d-alb --query 'LoadBalancers[0].DNSName' --output text
# Result: something like: infinityai-engine-d-alb-123456789.us-east-1.elb.amazonaws.com
```

## Step 2: Configure DNS Records in Namecheap

Log into your Namecheap account and navigate to **Domain List → Manage → Advanced DNS**.

### Required DNS Records

Configure the following DNS records:

| Type | Host | Value | TTL |
|------|------|--------|-----|
| A Record | @ | [Azure App Service IP] | 300 |
| CNAME Record | www | infinityai-pro.azurewebsites.net | 300 |
| CNAME Record | api | infinityai-engine-d-alb-[id].us-east-1.elb.amazonaws.com | 300 |
| CNAME Record | ai | [vercel-deployment-url] | 300 |

### Detailed Configuration Steps

#### 1. Main Domain (infinityai.pro)
- **Type**: A Record
- **Host**: @ (represents the root domain)
- **Value**: IP address of Azure App Service
- **TTL**: 300 seconds (5 minutes)

#### 2. WWW Subdomain (www.infinityai.pro)
- **Type**: CNAME Record
- **Host**: www
- **Value**: infinityai-pro.azurewebsites.net
- **TTL**: 300 seconds

#### 3. API Subdomain (api.infinityai.pro)
- **Type**: CNAME Record
- **Host**: api
- **Value**: Your AWS ALB DNS name (from Step 1)
- **TTL**: 300 seconds

#### 4. AI Gateway Subdomain (ai.infinityai.pro) - Optional
- **Type**: CNAME Record
- **Host**: ai
- **Value**: Your Vercel deployment URL
- **TTL**: 300 seconds

## Step 3: Verification Commands

After configuring DNS records, verify they're working:

```bash
# Check main domain
nslookup infinityai.pro

# Check www subdomain
nslookup www.infinityai.pro

# Check API subdomain
nslookup api.infinityai.pro

# Check if domains resolve correctly
curl -I https://infinityai.pro
curl -I https://api.infinityai.pro/health
```

## Step 4: SSL Certificate Configuration

### Azure App Service SSL
1. In Azure Portal, navigate to your App Service
2. Go to **Settings → Custom domains**
3. Add custom domain: `infinityai.pro` and `www.infinityai.pro`
4. Go to **Settings → TLS/SSL settings**
5. Create App Service Managed Certificate
6. Bind the certificate to your custom domains

### AWS Application Load Balancer SSL
1. In AWS Certificate Manager, request a certificate for `api.infinityai.pro`
2. Use DNS validation (add the CNAME record provided by ACM to Namecheap)
3. Once validated, attach the certificate to your ALB listener

## Step 5: DHAN API Configuration

In your DHAN API settings (https://dhanhq.co/api), configure:

### App Settings
- **Redirect URI**: `https://infinityai.pro/auth/callback`
- **Postback URL**: `https://api.infinityai.pro/auth/dhan/postback`

### Important Notes
- The Redirect URI is where users are sent after DHAN OAuth
- The Postback URL is where DHAN sends real-time updates
- These URLs are already configured in your deployed applications

## Step 6: Testing the Complete Setup

### 1. Test Frontend Access
```bash
# Main domain
curl -I https://infinityai.pro
# Should return: HTTP/2 200

# WWW redirect
curl -I https://www.infinityai.pro
# Should redirect to https://infinityai.pro
```

### 2. Test API Access
```bash
# Health check
curl https://api.infinityai.pro/health
# Should return: {"status": "healthy", "timestamp": "..."}

# API documentation
curl https://api.infinityai.pro/docs
# Should return the FastAPI documentation
```

### 3. Test DHAN Integration
1. Open `https://infinityai.pro` in your browser
2. Navigate to the token management section
3. Test the OAuth flow with DHAN
4. Verify that postback URL receives data (check AWS CloudWatch logs)

## Step 7: Monitoring and Troubleshooting

### DNS Propagation
- DNS changes can take up to 24-48 hours to fully propagate
- Use online DNS propagation checkers to monitor progress
- Test from different locations/devices

### Common Issues

#### "Domain not found" Error
- Check if A record is correctly pointing to Azure App Service IP
- Verify TTL settings (lower TTL = faster updates)

#### SSL Certificate Issues
- Ensure custom domain is properly added to Azure App Service
- Wait for certificate validation to complete
- Check certificate bindings

#### API Not Accessible
- Verify AWS ALB is running and healthy
- Check security groups allow HTTP/HTTPS traffic
- Confirm target group has healthy instances

### Useful Commands

```bash
# Check DNS propagation
dig infinityai.pro
dig api.infinityai.pro

# Test SSL certificates
openssl s_client -connect infinityai.pro:443
openssl s_client -connect api.infinityai.pro:443

# Check Azure App Service
az webapp show --name infinityai-pro --resource-group infinityai-rg

# Check AWS Load Balancer
aws elbv2 describe-load-balancers --names infinityai-engine-d-alb
```

## Final Configuration Summary

After completing all steps, your domains will work as follows:

- **https://infinityai.pro** → React Frontend (Azure)
- **https://www.infinityai.pro** → Redirects to main domain
- **https://api.infinityai.pro** → Engine D Backend (AWS)
- **https://ai.infinityai.pro** → AI Gateway (Vercel)

The DHAN API integration will use:
- **Redirect URI**: `https://infinityai.pro/auth/callback`
- **Postback URL**: `https://api.infinityai.pro/auth/dhan/postback`

Your system is now ready for production trading with secure, multi-cloud architecture!

## Support

If you encounter issues:
1. Check DNS propagation status
2. Verify SSL certificates are valid
3. Review Azure and AWS logs
4. Test DHAN API connectivity
5. Monitor health check endpoints