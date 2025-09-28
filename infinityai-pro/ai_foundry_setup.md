# Azure AI Foundry Resource Creation Guide

## 🎯 Current Step: Identity (Step 4 of 6)

You're creating an **Azure AI Foundry** resource - this is actually **better** than just OpenAI! It includes OpenAI plus additional AI capabilities.

### Identity Settings:
**Choose: "System assigned"**

### Why System assigned?
- ✅ **Automatic**: Azure manages the identity
- ✅ **Secure**: No manual key management
- ✅ **Integrated**: Works seamlessly with other Azure services
- ✅ **Simple**: Less configuration required

### What this enables:
- Your user gets **"Azure AI User"** role automatically
- Can develop with all projects under this resource
- Can use OpenAI, Vision, Speech, and other AI services

## 🚀 Continue to Tags (Step 5):

### Add these tags:
| Name | Value |
|------|-------|
| `Project` | `InfinityAI.Pro` |
| `Environment` | `Production` |
| `Service` | `AI-Foundry` |

## 🎯 Final Steps:

### Step 6: Review + Submit
1. **Review all settings**
2. **Click "Create"**
3. **Wait for deployment** (5-10 minutes)

### After Creation:
1. **Go to the resource**
2. **Navigate to "Keys and Endpoint"**
3. **Copy OpenAI endpoint and keys**

### Your Environment Variables:
```bash
AZURE_OPENAI_ENDPOINT=https://[your-resource].openai.azure.com/
AZURE_OPENAI_KEY=[your_key]
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo
```

## 💡 **Why AI Foundry is Better:**

Azure AI Foundry includes:
- ✅ **Azure OpenAI** (GPT-4, DALL-E)
- ✅ **Azure AI Vision** (image analysis)
- ✅ **Azure AI Speech** (transcription)
- ✅ **Azure AI Language** (sentiment analysis)
- ✅ **Model catalog** (pre-built models)
- ✅ **Prompt flow** (AI orchestration)

**This single resource replaces multiple separate services!** 🚀

**Select "System assigned" and continue!**</content>
<parameter name="filePath">/workspaces/InfinityAI.Pro/infinityai-pro/AZURE_AI_FOUNDRY_GUIDE.md