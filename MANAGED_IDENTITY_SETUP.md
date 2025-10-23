# Azure Managed Identity Setup Guide

This guide explains how to use **Azure Managed Identity** for authentication instead of storage keys and SAS tokens. Managed Identity provides a more secure and maintainable way to authenticate Azure services.

## Benefits of Managed Identity

✅ **No credential management** - No need to store or rotate storage account keys  
✅ **Better security** - Credentials never exposed in code or configuration  
✅ **Automatic rotation** - Azure handles credential lifecycle  
✅ **Simplified deployment** - Works seamlessly in Azure-hosted environments  
✅ **Audit trail** - Better tracking of which services access your resources

## Authentication Methods

This application supports **two authentication methods**:

### 1. Key-Based Authentication (Local Development)
- Uses `AZURE_STORAGE_CONNECTION_STRING` or `AZURE_STORAGE_ACCOUNT_KEY`
- Generates SAS tokens for blob access
- Best for local development and testing
- Requires storage keys in `.env` file

### 2. Managed Identity (Production/Azure-Hosted)
- Uses Azure Managed Identity credentials
- No SAS tokens needed - direct authentication
- Best for Azure App Service, Container Apps, Virtual Machines
- No storage keys required in configuration

## How It Works

### Auto-Detection
The application automatically detects which authentication method to use:
- **If `AZURE_STORAGE_CONNECTION_STRING` is set**: Uses key-based authentication
- **If `AZURE_STORAGE_CONNECTION_STRING` is NOT set**: Uses Managed Identity

### Manual Override
You can explicitly set the authentication method:
```bash
# In .env file
USE_MANAGED_IDENTITY=true   # Force Managed Identity
USE_MANAGED_IDENTITY=false  # Force key-based authentication
```

## Setup for Managed Identity

### Prerequisites
- Azure subscription
- Resource deployed to Azure (App Service, Container Apps, VM, etc.)
- Azure Storage Account
- Azure Translator Service

### Step 1: Enable System-Assigned Managed Identity

#### For Azure App Service / Web App:
```bash
az webapp identity assign \
  --name <your-app-name> \
  --resource-group <your-resource-group>
```

#### For Azure Container Apps:
```bash
az containerapp identity assign \
  --name <your-app-name> \
  --resource-group <your-resource-group> \
  --system-assigned
```

#### For Azure Virtual Machine:
```bash
az vm identity assign \
  --name <your-vm-name> \
  --resource-group <your-resource-group>
```

After running the command, you'll receive output containing the **Principal ID** (Object ID):
```json
{
  "principalId": "12345678-1234-1234-1234-123456789abc",
  "tenantId": "...",
  "type": "SystemAssigned"
}
```

### Step 2: Assign Required Azure Roles

The Managed Identity needs access to your storage account. Assign the **Storage Blob Data Contributor** role:

#### Using Azure Portal:
1. Navigate to your Storage Account
2. Click **Access Control (IAM)**
3. Click **+ Add** → **Add role assignment**
4. Select **Storage Blob Data Contributor** role
5. In the **Members** tab, select **Managed identity**
6. Click **+ Select members**
7. Find your App Service/Container App/VM
8. Click **Select** → **Review + assign**

#### Using Azure CLI:
```bash
# Get the storage account resource ID
STORAGE_ID=$(az storage account show \
  --name <storage-account-name> \
  --resource-group <storage-resource-group> \
  --query id --output tsv)

# Assign Storage Blob Data Contributor role
az role assignment create \
  --assignee <principal-id-from-step-1> \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID
```

### Step 3: Configure Environment Variables

In your Azure service, set these environment variables:

```bash
# Required
AZURE_TRANSLATOR_ENDPOINT=https://your-translator.cognitiveservices.azure.com/
AZURE_TRANSLATOR_KEY=your-translator-key
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-doc-intel-key
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account-name

# Enable Managed Identity
USE_MANAGED_IDENTITY=true

# NOT REQUIRED when using Managed Identity:
# AZURE_STORAGE_CONNECTION_STRING (omit this)
# AZURE_STORAGE_ACCOUNT_KEY (omit this)
```

#### Setting Environment Variables in Azure App Service:
```bash
az webapp config appsettings set \
  --name <your-app-name> \
  --resource-group <your-resource-group> \
  --settings \
    AZURE_TRANSLATOR_ENDPOINT="https://..." \
    AZURE_TRANSLATOR_KEY="..." \
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://..." \
    AZURE_DOCUMENT_INTELLIGENCE_KEY="..." \
    AZURE_STORAGE_ACCOUNT_NAME="your-storage-name" \
    USE_MANAGED_IDENTITY="true"
```

### Step 4: Deploy and Test

1. Deploy your application to Azure
2. The application will automatically use Managed Identity
3. Monitor logs to confirm successful authentication

## Role Requirements

| Azure Service | Required Role | Scope |
|--------------|---------------|-------|
| Storage Account | **Storage Blob Data Contributor** | Storage account level |
| Translator Service | (Uses API key for now) | N/A |
| Document Intelligence | (Uses API key for now) | N/A |

## Troubleshooting

### Error: "DefaultAzureCredential failed to retrieve a token"
**Cause**: Managed Identity not enabled or role not assigned  
**Solution**: 
- Verify Managed Identity is enabled (Step 1)
- Verify role assignment (Step 2)
- Wait 5-10 minutes for role propagation

### Error: "This request is not authorized to perform this operation"
**Cause**: Missing Storage Blob Data Contributor role  
**Solution**: Assign the role following Step 2

### Error: "Client address is not authorized"
**Cause**: Storage firewall blocking access  
**Solution**: 
- Add your Azure service's outbound IP to storage firewall
- Or enable "Allow Azure services on the trusted services list"

### Local Development Not Working
**Cause**: Managed Identity only works in Azure environments  
**Solution**: For local development:
1. Keep `USE_MANAGED_IDENTITY=false` or omit it
2. Use `AZURE_STORAGE_CONNECTION_STRING` in your `.env` file
3. Managed Identity will be used when deployed to Azure

## Best Practices

✅ **Use Managed Identity in production** - More secure, no key management  
✅ **Use key-based auth for local dev** - Easier to set up and test locally  
✅ **Don't commit keys to Git** - Always use `.env` for local credentials  
✅ **Enable monitoring** - Use Application Insights to track authentication issues  
✅ **Follow least privilege** - Only grant necessary permissions  
✅ **Test role assignments** - Verify access before full deployment

## Migration from Key-Based to Managed Identity

### Current Setup (Key-Based):
```bash
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=abc123...
```

### New Setup (Managed Identity):
```bash
# Remove these:
# AZURE_STORAGE_CONNECTION_STRING=...
# AZURE_STORAGE_ACCOUNT_KEY=...

# Keep only:
AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount
USE_MANAGED_IDENTITY=true
```

## Advanced: Using User-Assigned Managed Identity

If you need to use a **User-Assigned Managed Identity** instead of System-Assigned:

1. Create user-assigned identity:
```bash
az identity create \
  --name my-user-identity \
  --resource-group <resource-group>
```

2. Assign to your service:
```bash
az webapp identity assign \
  --name <app-name> \
  --resource-group <resource-group> \
  --identities <identity-resource-id>
```

3. Set client ID in environment:
```bash
AZURE_CLIENT_ID=<user-assigned-identity-client-id>
```

The `DefaultAzureCredential` will automatically detect and use it.

## Code Implementation Details

The application automatically handles both authentication methods:

```python
# In single_document_translation.py, batch_translation.py, ocr_translation_pipeline.py

def __init__(self, use_managed_identity=None):
    # Auto-detect: if no connection string, use Managed Identity
    if use_managed_identity is None:
        use_managed_identity = not bool(self.storage_connection_string)
    
    if self.use_managed_identity:
        # Use Managed Identity - no keys needed
        credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{self.storage_account_name}.blob.core.windows.net",
            credential=credential
        )
    else:
        # Use connection string or account key
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.storage_connection_string
        )
```

## Further Reading

- [What are managed identities for Azure resources?](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [Use managed identities in Azure App Service](https://learn.microsoft.com/azure/app-service/overview-managed-identity)
- [Authorize access to blobs using Microsoft Entra ID](https://learn.microsoft.com/azure/storage/blobs/authorize-access-azure-active-identity)
- [Azure Identity client library for Python](https://learn.microsoft.com/python/api/overview/azure/identity-readme)

## Support

If you encounter issues with Managed Identity setup:
1. Check Azure service logs for authentication errors
2. Verify role assignments in Azure Portal → Storage Account → Access Control (IAM)
3. Ensure Managed Identity is enabled on your compute resource
4. Wait 5-10 minutes after role assignment for changes to propagate
