# Azure Resource Naming Guide for InfinityAI.Pro

## 🎯 Resource Name for Azure OpenAI

When creating your Azure OpenAI resource, use this naming pattern:

### Recommended Name: `infinityai-pro-openai`

### Why this name?
- **Descriptive**: Clearly indicates it's for InfinityAI.Pro
- **Service-specific**: Shows it's for OpenAI
- **Valid format**: Only alphanumeric + hyphens, no leading/trailing hyphens
- **Unique**: Unlikely to conflict with other resources

### Alternative Options:
- `infinityai-openai`
- `infinityai-pro-ai`
- `infinityai-gpt4`
- `infinityai-llm`

### What happens with this name?
- **Endpoint**: `https://infinityai-pro-openai.openai.azure.com/`
- **Deployment URL**: `https://infinityai-pro-openai.openai.azure.com/openai/deployments/gpt-4-turbo/`
- **Easy to remember**: Clear and professional

### Azure Naming Rules:
✅ **Allowed**: Letters, numbers, hyphens
❌ **Not allowed**: Spaces, special characters, leading/trailing hyphens
✅ **Length**: 2-64 characters
✅ **Unique**: Must be globally unique across Azure

### Next Steps:
1. Use `infinityai-pro-openai` as your resource name
2. Note down the full endpoint URL after creation
3. Use this in your environment variables:
   ```
   AZURE_OPENAI_ENDPOINT=https://infinityai-pro-openai.openai.azure.com/
   ```

**Go ahead and create the resource with `infinityai-pro-openai`!** 🚀</content>
<parameter name="filePath">/workspaces/InfinityAI.Pro/infinityai-pro/AZURE_NAMING_GUIDE.md