# Azure Container Apps Internal Communication Investigation

## Current Status

### ✅ What's Working
1. **All services are running successfully**
   - Speaker Service: Running, database connected, listening on `0.0.0.0:8001`
   - API Gateway: Running, listening on port 3000
   - Draft Service: Running
   - RAG Service: Running

2. **All services are in the same Container Apps Environment**
   - Environment: `dg-backend-env`
   - Location: South India
   - All services share the same environment ID

3. **Ingress Configuration**
   - API Gateway: External (`external: true`), FQDN: `api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io`
   - Speaker Service: Internal (`external: false`), FQDN: `speaker-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`
   - Draft Service: Internal, FQDN: `draft-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`
   - RAG Service: Internal, FQDN: `rag-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`

### ❌ What's Not Working
**Internal Service Communication**: Services cannot communicate with each other using internal FQDNs.

**Symptoms**:
- API Gateway health check shows all backend services as "down" with 404 errors
- Accessing internal FQDNs from outside the environment returns 404
- Error: "Error 404 - This Container App is stopped or does not exist"

## Investigation Findings

### 1. Network Configuration
- **VNet Configuration**: `null` (using default Azure-managed networking)
- **Internal Load Balancer**: `null` (not explicitly configured)
- This is normal for Container Apps without custom VNet

### 2. Service Configuration
All services have correct:
- Target ports configured
- Ingress enabled
- Traffic routing to latest revision (100%)
- Running status: "Running"
- Provisioning state: "Provisioned"

### 3. Environment Variables
API Gateway has correct internal FQDNs:
```
SPEAKER_SERVICE_URL=https://speaker-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io
DRAFT_SERVICE_URL=https://draft-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io
RAG_SERVICE_URL=https://rag-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io
EVALUATION_SERVICE_URL=https://evaluation-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io
```

## Possible Root Causes

### 1. **Internal DNS Resolution Issue**
Azure Container Apps internal FQDNs (`.internal.*`) are only accessible from within the same Container Apps Environment. However, the 404 error suggests the DNS is resolving but the ingress is not routing correctly.

### 2. **Ingress Routing Configuration**
The internal ingress might not be properly configured to route traffic to the services. The 404 error page is coming from Azure Container Apps infrastructure, not from the services themselves.

### 3. **Service Readiness**
Although the services show as "Running", they might not be passing health checks or might not be ready to accept traffic through the ingress.

### 4. **HTTPS vs HTTP**
Internal services might need to use HTTP instead of HTTPS for internal communication.

## Recommended Next Steps

### Option 1: Try HTTP Instead of HTTPS
Update API Gateway environment variables to use `http://` instead of `https://` for internal services:
```bash
az containerapp update --name api-gateway --resource-group draftgenie-rg \
  --set-env-vars \
  "SPEAKER_SERVICE_URL=http://speaker-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io" \
  "DRAFT_SERVICE_URL=http://draft-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io" \
  "RAG_SERVICE_URL=http://rag-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io" \
  "EVALUATION_SERVICE_URL=http://evaluation-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io"
```

### Option 2: Use Simple Service Names
Try using just the service name without the full FQDN:
```bash
SPEAKER_SERVICE_URL=http://speaker-service
DRAFT_SERVICE_URL=http://draft-service
RAG_SERVICE_URL=http://rag-service
EVALUATION_SERVICE_URL=http://evaluation-service
```

### Option 3: Temporarily Make Services External
To test if the issue is with internal ingress, temporarily make services external:
```bash
az containerapp ingress update --name speaker-service --resource-group draftgenie-rg --type external
```

### Option 4: Check Service Health Endpoints
Verify that services are actually responding on their configured ports by checking container logs for incoming requests.

### Option 5: Review Azure Container Apps Documentation
Check if there are specific requirements for internal service communication that we're missing.

## Additional Information Needed

1. **Can we access services using simple names (without FQDN)?**
2. **Do internal services need HTTP instead of HTTPS?**
3. **Are there any Azure Container Apps quotas or limits being hit?**
4. **Is there a firewall or network policy blocking internal traffic?**

## References

- Azure Container Apps Documentation: https://learn.microsoft.com/en-us/azure/container-apps/
- Internal Ingress: https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview
- Service Discovery: https://learn.microsoft.com/en-us/azure/container-apps/connect-apps

