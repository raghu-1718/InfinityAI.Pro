# Storing & Rotating Dhan Secrets (AWS + optional GCP)

This guide shows how to securely store Dhan API credentials and rotating access-tokens using cloud secret stores.

## Files
- `scripts/store-dhan-secrets.ps1` — Store or update the secret in AWS and/or GCP.
- `scripts/verify-backend-extended.ps1` — Run health checks and (optionally) POST a validation payload to the Dhan webhook path.

## Pre‑requisites
- Run locally (not in public CI) using your admin/dev machine.
- AWS CLI configured with an IAM principal that has:
  - `secretsmanager:CreateSecret`
  - `secretsmanager:PutSecretValue`
  - `secretsmanager:DescribeSecret`
  - `secretsmanager:GetSecretValue`
- If using GCP: gcloud configured with a principal that has:
  - `secretmanager.secrets.create`
  - `secretmanager.versions.add`

## Recommended secret names
- AWS Secrets Manager: `prod/dhan/api`
- GCP Secret Manager: `prod-dhan-api`

## Secret payload (JSON)
```json
{
  "dhan_api_key": "<KEY>",
  "dhan_api_secret": "<SECRET>",
  "dhan_access_token": "<DAILY_TOKEN>"
}
```

## Usage

AWS only:
```powershell
.\scripts\store-dhan-secrets.ps1 -Mode aws -SecretName "prod/dhan/api" -PromptForSecrets
```

AWS + GCP:
```powershell
.\scripts\store-dhan-secrets.ps1 -Mode all -SecretName "prod/dhan/api" -GcpSecretName "prod-dhan-api" -PromptForSecrets
```

Verify endpoints (and optionally POST a test webhook):
```powershell
.\scripts\verify-backend-extended.ps1 -BaseUrl "https://<ALB>" -DoWebhookTest
```

## Backend integration tips
- Engine C: on boot, call `GetSecretValue` and populate in-memory config.
- When `POST /engine-c/user/broker/dhan/token` is called, validate the token and update the secret store.
- Do NOT log secret values or return them in any API responses.

## Minimal IAM policies

Backend role (read-only at runtime):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SecretsReadOnly",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:<region>:<account-id>:secret:prod/dhan/api*"
    }
  ]
}
```

Operator (update):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SecretsUpdate",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:PutSecretValue",
        "secretsmanager:CreateSecret",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:<region>:<account-id>:secret:prod/dhan/api*"
    }
  ]
}
```

## Safety checklist
- Rotate any keys that were accidentally exposed.
- Confirm IAM policies are least‑privilege.
- Confirm ALB/WAF protections and rate‑limits for `/engine-c/webhooks/dhan/postback`.
