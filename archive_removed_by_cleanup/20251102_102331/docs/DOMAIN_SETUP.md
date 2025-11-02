# InfinityAI.Pro Domain and CDN Setup

This guide wires infinityai.pro to a secure CDN and routes frontend and API traffic to the right backends.

## What you get
- TLS cert (ACM, DNS-validated)
- CloudFront distribution with two origins:
  - S3 static website for the React frontend
  - ALB for Engine C/D APIs and WebSockets
- Route 53 alias records for apex and www -> CloudFront
- Path-based routing at CDN: `/engine-c/*` and `/engine-d/*` -> ALB; everything else -> S3

## Prerequisites
- Public hosted zone in Route 53: `infinityai.pro`
- S3 website hosting enabled for your bucket (e.g., `infinityai-pro-frontend.s3-website-us-east-1.amazonaws.com`)
- An ALB DNS name (e.g., `infinityai-alb-XXXX.us-east-1.elb.amazonaws.com`) already routing to Engine C/D services.
- AWS CLI logged in and default region set to `us-east-1` (CloudFront certs must be in us-east-1)

## Deploy (PowerShell)

```pwsh
# From repo root or deploy/aws folder
cd deploy/aws

# Fill these with your actual values
$Stack = "infinityai-pro-cdn"
$Domain = "infinityai.pro"
$ZoneId = "<ROUTE53_HOSTED_ZONE_ID>"
$Bucket = "infinityai-pro-frontend"
$S3Website = "infinityai-pro-frontend.s3-website-us-east-1.amazonaws.com"
$ALB = "infinityai-alb-124143296.us-east-1.elb.amazonaws.com"

./deploy-cloudfront.ps1 -StackName $Stack -DomainName $Domain -HostedZoneId $ZoneId -S3BucketName $Bucket -S3WebsiteDomainName $S3Website -ALBDomainName $ALB
```

Wait 10–20 minutes for CloudFront to deploy. The stack outputs include the distribution domain.

## Frontend config
After CloudFront is ready, the site is accessible at:
- https://infinityai.pro
- https://www.infinityai.pro

The frontend is already configured (via `api-config.js` change) to call APIs via the same origin, so API requests go to `https://infinityai.pro/engine-d/...` etc.

## Dhan integration
Set these in Dhan developer portal:
- Redirect URL: `https://infinityai.pro/engine-c/auth/dhan/callback`
- Postback URL: `https://infinityai.pro/engine-c/webhooks/dhan/postback`

## Optional: GCP Cloud Run subdomains
If you want direct subdomains for A/B (not required for the app, Engine D proxies):
- Create Google-managed cert for `a.infinityai.pro` and `b.infinityai.pro`
- Map Cloud Run service custom domains and add the provided CNAMEs in Route 53

## Troubleshooting
- 403 from S3 origin: ensure bucket website hosting is enabled, index document `index.html` exists, and CloudFront Behavior default points to S3WebsiteOrigin.
- 502/503 on API paths: confirm ALB target groups are healthy, and CloudFront CacheBehavior for `engine-d/*` & `engine-c/*` points to the ALB origin with caching disabled.
- WebSockets: CF passes through. Ensure your client builds WS URLs from `window.location`.

## Verification
Run the backend verify script against the new domain:

```pwsh
cd scripts
./verify-backend-extended.ps1 -BaseUrl "https://infinityai.pro"
```

Then load https://infinityai.pro and sign in; check Dhan status and market widgets.
