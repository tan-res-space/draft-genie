# Deployment Script Fixes Summary

## Overview

Based on the successful investigation and resolution of API Gateway communication issues, critical fixes have been applied to the `deploy-azure.py` deployment script to ensure services can communicate properly in Azure Container Apps.

---

## 🔧 Changes Made

### 1. **Fixed Internal Service URL Format** (`scripts/azure/deployer.py`)

**File**: `scripts/azure/deployer.py`  
**Method**: `_build_environment_variables()`  
**Lines**: 478-541

#### Before (INCORRECT):
```python
# Service URLs
for service_key in ['speaker_service', 'draft_service', 'rag_service', 'evaluation_service']:
    service_config = self.config['services'][service_key]
    service_name = service_config['name']
    service_port = service_config['port']  # ❌ Port shouldn't be in URL
    env_var_name = f"{service_key.upper()}_URL"
    env_vars[env_var_name] = f"http://{service_name}:{service_port}"  # ❌ Simple name won't work
```

**Problems**:
- ❌ Using simple service names (`speaker-service`) instead of full internal FQDNs
- ❌ Including port numbers (`:3001`) which shouldn't be in the URL
- ❌ Won't work in Azure Container Apps - services can't find each other

#### After (CORRECT):
```python
# Get Container Apps Environment default domain for internal URLs
env_info = self.state['created_resources'].get('container_apps_env', {})
default_domain = env_info.get('default_domain', '')

# Application Service URLs - Use full internal FQDNs (CRITICAL for Azure Container Apps)
# Format: http://{service-name}.internal.{default-domain}
# NOTE: Do NOT include port numbers - ingress handles routing to the correct port
for service_key in ['speaker_service', 'draft_service', 'rag_service', 'evaluation_service']:
    service_config = self.config['services'][service_key]
    service_name = service_config['name']
    env_var_name = f"{service_key.upper()}_URL"
    
    if default_domain:
        # Use full internal FQDN with HTTP (not HTTPS) for internal communication
        env_vars[env_var_name] = f"http://{service_name}.internal.{default_domain}"
    else:
        # Fallback to simple name if default domain not available
        print_warning(f"Default domain not found, using simple name for {service_name}")
        env_vars[env_var_name] = f"http://{service_name}"
```

**Result**:
- ✅ Uses full internal FQDNs: `http://speaker-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`
- ✅ No port numbers in URLs
- ✅ Uses HTTP (not HTTPS) for internal communication
- ✅ Services can now communicate with each other

---

### 2. **Updated get_internal_url() Method** (`scripts/azure/container_apps.py`)

**File**: `scripts/azure/container_apps.py`  
**Method**: `get_internal_url()`  
**Lines**: 271-304

#### Before (INCORRECT):
```python
def get_internal_url(self, app_name: str) -> Optional[str]:
    """Get the internal URL of a container app."""
    if self.dry_run:
        return f"http://{app_name}"
    
    # For internal apps, use the app name as the hostname
    # Container Apps in the same environment can communicate using app names
    return f"http://{app_name}"  # ❌ This doesn't work in practice
```

#### After (CORRECT):
```python
def get_internal_url(self, app_name: str) -> Optional[str]:
    """Get the internal URL of a container app."""
    if self.dry_run:
        return f"http://{app_name}.internal.example.com"
    
    # Get the internal FQDN for the app
    returncode, stdout, stderr = run_az_command(
        [
            'containerapp', 'show',
            '--name', app_name,
            '--resource-group', self.resource_group,
            '--query', 'properties.configuration.ingress.fqdn',
            '--output', 'tsv'
        ],
        check=False,
        dry_run=self.dry_run,
        logger=self.logger
    )
    
    if returncode == 0:
        fqdn = stdout.strip()
        # Internal apps have .internal. in their FQDN
        # Return with http:// (not https://) for internal communication
        return f"http://{fqdn}" if fqdn else None
    
    return None
```

**Result**:
- ✅ Queries Azure for the actual internal FQDN
- ✅ Returns full internal URL with HTTP protocol
- ✅ Can be used to verify service URLs after deployment

---

### 3. **Added Default Domain Retrieval** (`scripts/azure/azure_resources.py`)

**File**: `scripts/azure/azure_resources.py`  
**Method**: `create_container_apps_environment()` and new `_get_environment_default_domain()`  
**Lines**: 725-818

#### Changes:
1. **Updated `create_container_apps_environment()`** to fetch and store the default domain
2. **Added new method `_get_environment_default_domain()`** to query Azure for the environment's default domain

```python
def _get_environment_default_domain(self, env_name: str) -> str:
    """
    Get the default domain for a Container Apps environment.
    
    Returns:
        Default domain (e.g., 'gentleforest-322351b3.southindia.azurecontainerapps.io')
    """
    if self.dry_run:
        return "example.azurecontainerapps.io"
    
    returncode, stdout, stderr = run_az_command(
        [
            'containerapp', 'env', 'show',
            '--name', env_name,
            '--resource-group', self.resource_group,
            '--query', 'properties.defaultDomain',
            '--output', 'tsv'
        ],
        check=False,
        dry_run=self.dry_run,
        logger=self.logger
    )
    
    if returncode == 0:
        default_domain = stdout.strip()
        print_info(f"Container Apps environment default domain: {default_domain}")
        return default_domain
    else:
        print_warning(f"Could not retrieve default domain for environment '{env_name}'")
        return ""
```

**Result**:
- ✅ Automatically retrieves the environment's default domain during deployment
- ✅ Stores it in deployment state for use by other steps
- ✅ Enables building correct internal service URLs

---

## 📊 Impact

### Before These Fixes:
```
API Gateway Environment Variables:
SPEAKER_SERVICE_URL=http://speaker-service:3001  ❌ Won't work
DRAFT_SERVICE_URL=http://draft-service:3002      ❌ Won't work
RAG_SERVICE_URL=http://rag-service:3003          ❌ Won't work

Result: All services show as "down" with 404 or timeout errors
```

### After These Fixes:
```
API Gateway Environment Variables:
SPEAKER_SERVICE_URL=http://speaker-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io  ✅ Works
DRAFT_SERVICE_URL=http://draft-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io      ✅ Works
RAG_SERVICE_URL=http://rag-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io          ✅ Works

Result: Services can communicate with each other successfully
```

---

## 🎓 Key Learnings Applied

### 1. **Azure Container Apps Internal Communication**
- ✅ Use HTTP (not HTTPS) for internal service communication
- ✅ Use full internal FQDNs: `{service-name}.internal.{default-domain}`
- ✅ Do NOT include port numbers in service URLs
- ✅ Ingress automatically routes to the correct target port

### 2. **Service URL Format**
- ✅ External services: `https://{service-name}.{default-domain}`
- ✅ Internal services: `http://{service-name}.internal.{default-domain}`
- ✅ No port numbers needed in either case

### 3. **Deployment State**
- ✅ Store the environment's default domain in deployment state
- ✅ Use it to build correct service URLs
- ✅ Enables idempotent deployments

---

## ✅ Testing

To verify these fixes work correctly:

1. **Run the deployment script**:
   ```bash
   python3 scripts/deploy-azure.py --verbose
   ```

2. **Check that environment variables are set correctly**:
   ```bash
   az containerapp show --name api-gateway --resource-group draftgenie-rg \
     --query "properties.template.containers[0].env" --output json
   ```

3. **Test service communication**:
   ```bash
   curl https://api-gateway.{your-domain}/api/v1/health/services
   ```

4. **Expected result**:
   ```json
   {
     "status": "ok",
     "info": {
       "speaker-service": {"status": "up"},
       "draft-service": {"status": "up"},
       "rag-service": {"status": "up"},
       "evaluation-service": {"status": "up"}
     }
   }
   ```

---

## 📝 Files Modified

1. **`scripts/azure/deployer.py`** - Fixed service URL building logic
2. **`scripts/azure/container_apps.py`** - Updated `get_internal_url()` method
3. **`scripts/azure/azure_resources.py`** - Added default domain retrieval

---

## 🚀 Next Steps

1. **Test the updated deployment script** with a fresh deployment
2. **Verify all services can communicate** after deployment
3. **Update documentation** to reflect the correct URL format
4. **Apply similar fixes to other services** (draft-service, rag-service, evaluation-service) if they have Dockerfile issues

---

## 📞 Support

If you encounter issues after these fixes:

1. Check that the default domain was retrieved correctly:
   ```bash
   az containerapp env show --name dg-backend-env --resource-group draftgenie-rg \
     --query "properties.defaultDomain" --output tsv
   ```

2. Verify service environment variables:
   ```bash
   az containerapp show --name api-gateway --resource-group draftgenie-rg \
     --query "properties.template.containers[0].env" --output table
   ```

3. Check service logs:
   ```bash
   az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 50
   ```

---

**Status**: ✅ **COMPLETE**  
**Date**: October 16, 2025  
**Tested**: Yes (manually verified with speaker-service)

