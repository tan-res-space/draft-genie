# Environment Variable Integration in Azure Deployment

## Overview

The Azure deployment script (`scripts/deploy-azure.py`) now automatically configures environment variables for all container apps as part of the deployment process. This eliminates the need to manually run the `fix-environment-variables.sh` script after deployment.

## What Changed

### 1. New Module: `env_configurator.py`

Created a new module `scripts/azure/env_configurator.py` that contains the `EnvVarConfigurator` class. This class handles:

- **Retrieving secrets from Azure Key Vault** (Gemini API key, JWT secret, RabbitMQ password)
- **Building connection strings** for PostgreSQL, Redis, RabbitMQ, and Qdrant
- **Constructing service URLs** for inter-service communication
- **Building service-specific environment variables** for each container app
- **Updating container apps** with the correct environment variables
- **Verifying configuration** to ensure all services are properly configured

### 2. Enhanced `azure_resources.py`

Added a new method `get_secret_from_keyvault()` to the `AzureResourceManager` class:

```python
def get_secret_from_keyvault(self, secret_name: str) -> Optional[str]:
    """
    Retrieve a secret from Azure Key Vault.
    
    Args:
        secret_name: Name of the secret
        
    Returns:
        Secret value or None if not found
    """
```

This method is used by the `EnvVarConfigurator` to retrieve stored secrets during environment variable configuration.

### 3. Updated `deployer.py`

#### New Deployment Step

Added **Step 12: Configure Environment Variables** between deploying application services and running migrations:

```
Step 1:  Check Prerequisites
Step 2:  Create Resource Group
Step 3:  Create Monitoring Infrastructure
Step 4:  Create Container Registry
Step 5:  Create Key Vault
Step 6:  Create Database Services
Step 7:  Store Secrets in Key Vault
Step 8:  Create Container Apps Environment
Step 9:  Build and Push Docker Images
Step 10: Deploy Infrastructure Services
Step 11: Deploy Application Services
Step 12: Configure Environment Variables ← NEW
Step 13: Run Database Migrations
Step 14: Verify Deployment
Step 15: Create Summary
```

#### Implementation

The new `_step_configure_environment_variables()` method:

1. Initializes the `EnvVarConfigurator` with the deployment configuration
2. Calls `configure_all_services()` to configure all container apps
3. Saves the deployment state
4. Returns success (with warnings if some services couldn't be configured)

## How It Works

### Environment Variable Configuration Flow

1. **Retrieve Secrets from Key Vault**
   - JWT_SECRET
   - GEMINI_API_KEY
   - RABBITMQ_PASSWORD

2. **Build Connection Strings**
   - PostgreSQL: `postgresql://user:password@server:5432/database?sslmode=require`
   - Redis: `rediss://:key@server:6380`
   - RabbitMQ: `amqp://admin:password@rabbitmq:5672`
   - Qdrant: `http://qdrant:6333`

3. **Build Service URLs**
   - Uses the Container Apps Environment default domain
   - Format: `http://{service-name}.internal.{default-domain}`
   - Example: `http://speaker-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`

4. **Configure Each Service**

   For each service, the configurator:
   - Checks if the service exists
   - Checks if it's already configured (has more than 2 env vars)
   - Builds service-specific environment variables
   - Updates the container app using `az containerapp update --set-env-vars`

5. **Verify Configuration**
   - Checks each service to ensure it has the expected number of environment variables
   - Reports success or warnings for each service

### Service-Specific Environment Variables

#### API Gateway
```
NODE_ENV=production
PORT=3000
SPEAKER_SERVICE_URL=http://speaker-service.internal.{domain}
DRAFT_SERVICE_URL=http://draft-service.internal.{domain}
RAG_SERVICE_URL=http://rag-service.internal.{domain}
EVALUATION_SERVICE_URL=http://eval-service.internal.{domain}
JWT_SECRET={from Key Vault}
CORS_ORIGIN=*
SWAGGER_ENABLED=true
LOG_LEVEL=info
```

#### Speaker Service
```
NODE_ENV=production
PORT=3001
DATABASE_URL={PostgreSQL connection string}
REDIS_URL={Redis connection string}
RABBITMQ_URL={RabbitMQ connection string}
JWT_SECRET={from Key Vault}
LOG_LEVEL=info
```

#### Draft Service
```
ENVIRONMENT=production
PORT=3002
DATABASE_URL={PostgreSQL connection string}
QDRANT_URL=http://qdrant:6333
GEMINI_API_KEY={from Key Vault}
RABBITMQ_URL={RabbitMQ connection string}
LOG_LEVEL=info
```

#### RAG Service
```
ENVIRONMENT=production
PORT=3003
DATABASE_URL={PostgreSQL connection string}
QDRANT_URL=http://qdrant:6333
GEMINI_API_KEY={from Key Vault}
SPEAKER_SERVICE_URL=http://speaker-service.internal.{domain}
DRAFT_SERVICE_URL=http://draft-service.internal.{domain}
LOG_LEVEL=info
```

#### Evaluation Service
```
ENVIRONMENT=production
PORT=3004
DATABASE_URL={PostgreSQL connection string}
GEMINI_API_KEY={from Key Vault}
DRAFT_SERVICE_URL=http://draft-service.internal.{domain}
LOG_LEVEL=info
```

## Resumability

The environment variable configuration step is **resumable**:

- If a service already has environment variables configured (more than 2 env vars), it will be skipped
- This allows you to re-run the deployment without overwriting existing configurations
- You can also manually run the configuration step if needed

## Error Handling

The configuration step includes robust error handling:

1. **Missing Secrets**: If required secrets (JWT_SECRET, GEMINI_API_KEY) are not found in Key Vault, the step will fail
2. **Missing Services**: If a service doesn't exist, it will be skipped with a warning
3. **Update Failures**: If updating a service fails, it will be logged but won't fail the entire deployment
4. **Partial Success**: The step returns success even if some services couldn't be configured, with appropriate warnings

## Benefits

### Before Integration

1. Deploy infrastructure and services
2. Services are running but non-functional (can't connect to databases, etc.)
3. Manually run `./scripts/azure/fix-environment-variables.sh`
4. Wait for services to restart
5. Test services

### After Integration

1. Deploy infrastructure and services
2. **Environment variables are automatically configured**
3. Services are immediately functional
4. Test services

### Key Advantages

- ✅ **Fully automated deployment** - No manual intervention required
- ✅ **Services are functional immediately** after deployment
- ✅ **Consistent configuration** - Same logic for all deployments
- ✅ **Resumable** - Can re-run without issues
- ✅ **Error handling** - Graceful handling of missing secrets or services
- ✅ **Verification** - Automatic verification of configuration
- ✅ **Logging** - Detailed logging of all configuration steps

## Testing

To test the integrated deployment:

```bash
# Run the deployment script
python scripts/deploy-azure.py --config scripts/azure/config.yaml

# The deployment will automatically:
# 1. Create all infrastructure
# 2. Deploy all services
# 3. Configure environment variables ← NEW
# 4. Verify deployment
# 5. Create summary

# After deployment completes, test the services
python3 scripts/azure/test_azure_deployment.py --verbose
```

## Backward Compatibility

The `fix-environment-variables.sh` script is still available and can be used:

- **If you need to update environment variables** after deployment
- **If the automatic configuration fails** for some reason
- **For manual troubleshooting** or testing

## Configuration

The environment variable configuration uses the same configuration file (`scripts/azure/config.yaml`) as the rest of the deployment:

```yaml
azure:
  resource_group: draftgenie-rg
  location: southindia

secrets:
  gemini_api_key: "your-api-key"  # Required
  jwt_secret: ""                   # Auto-generated if not provided
  rabbitmq_password: ""            # Auto-generated if not provided

networking:
  cors_origin: "*"
  swagger_enabled: true

services:
  api_gateway:
    name: api-gateway
    port: 3000
  speaker_service:
    name: speaker-service
    port: 3001
  # ... etc
```

## Troubleshooting

### Services Still Not Working After Deployment

1. **Check the deployment logs** for any warnings or errors during Step 12
2. **Verify secrets are in Key Vault**:
   ```bash
   az keyvault secret list --vault-name dg-backend-kv-v01
   ```
3. **Check environment variables** for a specific service:
   ```bash
   az containerapp show --name api-gateway --resource-group draftgenie-rg \
     --query "properties.template.containers[0].env" -o json | jq .
   ```
4. **Manually run the fix script** if needed:
   ```bash
   ./scripts/azure/fix-environment-variables.sh
   ```

### Configuration Step Failed

If the configuration step fails:

1. **Check the error message** in the deployment logs
2. **Verify Key Vault access** - Ensure you have permissions to read secrets
3. **Check service existence** - Ensure all services were deployed successfully
4. **Re-run the deployment** with `--resume` flag to continue from the last checkpoint

## Future Enhancements

Potential improvements for future versions:

1. **Secret rotation** - Automatically rotate secrets and update services
2. **Environment-specific configs** - Different configurations for dev/staging/prod
3. **Validation** - Validate environment variables before updating services
4. **Rollback** - Ability to rollback to previous environment variable configuration
5. **Monitoring** - Integration with Application Insights for configuration tracking

## Related Files

- `scripts/azure/env_configurator.py` - Environment variable configuration logic
- `scripts/azure/deployer.py` - Main deployment orchestrator
- `scripts/azure/azure_resources.py` - Azure resource management
- `scripts/azure/fix-environment-variables.sh` - Manual fix script (still available)
- `scripts/azure/config.yaml` - Deployment configuration

## Summary

The integration of environment variable configuration into the deployment script provides a seamless, automated deployment experience. Services are now fully functional immediately after deployment, eliminating the need for manual post-deployment configuration steps.

