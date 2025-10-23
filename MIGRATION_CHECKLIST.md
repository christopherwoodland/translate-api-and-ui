# Quick Start: Managed Identity Migration

## Current Status: ✅ Implementation Complete

All code has been updated to support Azure Managed Identity authentication. Your application can now work in two modes:

## Local Development (Current Setup)
Your current `.env` configuration with storage connection string will continue to work exactly as before:

```bash
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=aistgvi;...
USE_MANAGED_IDENTITY=false  # or omit this line
```

**No action required for local development** - everything works as before.

## Azure Production (Optional Upgrade)

When you're ready to deploy to Azure with improved security, follow these steps:

### ✅ Step 1: Deploy to Azure
Deploy your application to:
- Azure App Service, or
- Azure Container Apps, or
- Azure Virtual Machine

### ✅ Step 2: Enable Managed Identity (2 minutes)

**Via Azure Portal:**
1. Go to your App Service/Container App
2. Navigate to **Identity** section
3. Under **System assigned**, toggle to **On**
4. Click **Save**
5. Copy the **Object (principal) ID** that appears

**Via Azure CLI:**
```bash
az webapp identity assign \
  --name your-app-name \
  --resource-group your-resource-group
```

### ✅ Step 3: Grant Storage Access (3 minutes)

**Via Azure Portal:**
1. Go to your Storage Account: **aistgvi**
2. Click **Access Control (IAM)** in left menu
3. Click **+ Add** → **Add role assignment**
4. Select role: **Storage Blob Data Contributor**
5. Click **Next**
6. Click **+ Select members**
7. Search for your app name
8. Select it and click **Select**
9. Click **Review + assign**

**Via Azure CLI:**
```bash
# Get storage account resource ID
STORAGE_ID=$(az storage account show \
  --name aistgvi \
  --resource-group <your-storage-resource-group> \
  --query id --output tsv)

# Assign role (use the principal ID from Step 2)
az role assignment create \
  --assignee <principal-id-from-step-2> \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID
```

### ✅ Step 4: Update Environment Variables (1 minute)

In your Azure App Service Configuration:

**Keep these:**
```bash
AZURE_TRANSLATOR_ENDPOINT=https://cwtrans001.cognitiveservices.azure.com/
AZURE_TRANSLATOR_KEY=<your-key>
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://doc-intel-behavioral-health.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=<your-key>
AZURE_STORAGE_ACCOUNT_NAME=aistgvi
```

**Add this:**
```bash
USE_MANAGED_IDENTITY=true
```

**Remove these (no longer needed):**
```bash
# AZURE_STORAGE_CONNECTION_STRING=...  <- DELETE
# AZURE_STORAGE_ACCOUNT_KEY=...  <- DELETE
```

**Via Azure CLI:**
```bash
az webapp config appsettings set \
  --name your-app-name \
  --resource-group your-resource-group \
  --settings USE_MANAGED_IDENTITY=true
```

### ✅ Step 5: Test (5 minutes)

1. Restart your app
2. Upload a test PDF
3. Run a translation
4. Check logs for any errors

**Expected log message:**
```
Using Azure Managed Identity for authentication
```

## Benefits You'll Get

✅ **Security**: No storage keys in your configuration  
✅ **Compliance**: Better audit trail with Azure AD  
✅ **Simplicity**: No key rotation needed  
✅ **Reliability**: Credentials never expire  

## Troubleshooting

### "DefaultAzureCredential failed to retrieve a token"
- Wait 5-10 minutes after role assignment
- Verify Managed Identity is enabled
- Check role assignment in Storage Account → IAM

### "This request is not authorized"
- Verify role is **Storage Blob Data Contributor** (not just Blob Reader)
- Check the role is assigned to your app's Managed Identity

### Still getting errors?
- Check Application Insights or App Service logs
- Verify the principal ID matches
- Try removing and re-adding the role assignment

## Rollback Plan

If you need to rollback to key-based authentication:

1. Set `USE_MANAGED_IDENTITY=false` in app settings
2. Add back `AZURE_STORAGE_CONNECTION_STRING`
3. Restart the app

The code automatically detects and switches back.

## Timeline Estimate

| Task | Time | Complexity |
|------|------|------------|
| Deploy to Azure | 10-15 min | ⚪ Easy |
| Enable Managed Identity | 2 min | ⚪ Easy |
| Assign Storage Role | 3 min | ⚪ Easy |
| Update Environment Variables | 1 min | ⚪ Easy |
| Test Translations | 5 min | ⚪ Easy |
| **Total** | **~25 min** | ⚪ **Easy** |

## Documentation

- **Full Setup Guide**: See `MANAGED_IDENTITY_SETUP.md`
- **Implementation Details**: See `MANAGED_IDENTITY_SUMMARY.md`
- **Azure Docs**: [Managed Identities Overview](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)

## Questions?

Common questions:

**Q: Do I need to change anything for local development?**  
A: No, your current setup continues to work.

**Q: Can I test Managed Identity locally?**  
A: No, Managed Identity only works in Azure. Use key-based auth locally.

**Q: Will this break my current deployment?**  
A: No, it's backward compatible. Old deployments continue working.

**Q: Do I need to update all environments at once?**  
A: No, you can migrate per environment (dev → staging → production).

**Q: What if I want to switch back?**  
A: Just set `USE_MANAGED_IDENTITY=false` and add back the connection string.

---

**Status**: ✅ Code Ready  
**Action Required**: Deploy to Azure when ready  
**Risk Level**: 🟢 Low (fully backward compatible)
