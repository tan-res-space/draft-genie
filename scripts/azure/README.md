# DraftGenie Azure Deployment Scripts

Automated deployment scripts for deploying DraftGenie to Microsoft Azure.

## Overview

This directory contains Python scripts that automate the complete deployment process outlined in `docs/deployment/azure-deployment-guide.md`. The scripts are modular, interactive, and production-ready.

## Features

✅ **Fully Automated** - Deploy DraftGenie with a single command  
✅ **Interactive Configuration** - Guided setup wizard for first-time users  
✅ **Resumable** - Continue from last checkpoint if deployment fails  
✅ **Dry Run Mode** - Preview deployment without creating resources  
✅ **Modular Design** - Each deployment phase is a separate module  
✅ **Error Handling** - Robust error handling with detailed logging  
✅ **State Management** - Saves deployment state for resume capability  
✅ **Secrets Management** - Secure handling of passwords and API keys  

## Prerequisites

### Required Tools

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **Azure CLI**
   ```bash
   # macOS
   brew install azure-cli
   
   # Windows
   # Download from https://aka.ms/installazurecliwindows
   
   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

3. **Docker**
   ```bash
   # Download from https://www.docker.com/products/docker-desktop
   ```

4. **Git**
   ```bash
   git --version
   ```

### Required Python Packages

**Option 1: Using Virtual Environment (Recommended)**

```bash
# Set up virtual environment and install dependencies
bash scripts/setup-venv.sh

# Activate virtual environment
source scripts/venv/bin/activate
```

**Option 2: Global Installation**

```bash
pip install pyyaml
```

**Why use a virtual environment?**
- Keeps dependencies isolated from system Python
- Prevents version conflicts with other projects
- Easy to recreate if something goes wrong
- Automatically excluded from git

### Azure Account

- Active Azure subscription
- Logged in to Azure CLI: `az login`

### API Keys

- **Google Gemini API Key** (required)
  - Get from: https://makersuite.google.com/app/apikey

## Quick Start

### 1. Interactive Deployment (Recommended for First-Time Users)

```bash
# Set up virtual environment (recommended)
bash scripts/setup-venv.sh
source scripts/venv/bin/activate

# Run the deployment script
python scripts/deploy-azure.py

# The script will:
# 1. Guide you through configuration setup
# 2. Validate prerequisites
# 3. Create all Azure resources
# 4. Build and push Docker images
# 5. Deploy all services
# 6. Verify deployment

# When done, deactivate virtual environment
deactivate
```

### 2. Using a Configuration File

```bash
# Copy the template
cp scripts/azure/config.template.yaml scripts/azure/config.yaml

# Edit the configuration
nano scripts/azure/config.yaml

# Run deployment
python scripts/deploy-azure.py --config scripts/azure/config.yaml
```

### 3. Dry Run (Preview Without Creating Resources)

```bash
python scripts/deploy-azure.py --dry-run
```

### 4. Resume from Checkpoint

```bash
# If deployment fails, resume from last successful step
python scripts/deploy-azure.py --resume
```

## Configuration

### Configuration File Structure

The configuration file (`config.yaml`) contains all deployment settings:

```yaml
azure:
  subscription_id: ""           # Azure subscription (optional)
  resource_group: "draftgenie-rg"
  location: "eastus"
  project_name: "draftgenie"

container_registry:
  name: "draftgenieacr"         # Must be globally unique
  sku: "Basic"

key_vault:
  name: "draftgenie-kv"         # Must be globally unique

postgresql:
  server_name: "draftgenie-postgres"
  database_name: "draftgenie"
  admin_user: "draftgenie"
  sku: "Standard_B1ms"

redis:
  name: "draftgenie-redis"
  sku: "Basic"
  vm_size: "c0"

secrets:
  gemini_api_key: "your-key-here"  # Required
  jwt_secret: ""                    # Auto-generated if empty
  rabbitmq_password: ""             # Auto-generated if empty
```

See `config.template.yaml` for complete configuration options.

### Required Configuration

The following fields are **required**:

- `azure.resource_group` - Resource group name
- `azure.location` - Azure region (e.g., eastus, westus2)
- `container_registry.name` - Globally unique ACR name (alphanumeric only)
- `key_vault.name` - Globally unique Key Vault name
- `secrets.gemini_api_key` - Google Gemini API key

### Auto-Generated Values

The following values are auto-generated if not provided:

- PostgreSQL admin password
- JWT secret
- RabbitMQ password

All auto-generated secrets are stored in Azure Key Vault.

## Command Line Options

```bash
python scripts/deploy-azure.py [OPTIONS]

Options:
  --config PATH       Path to configuration file (default: scripts/azure/config.yaml)
  --dry-run          Preview deployment without creating resources
  --verbose          Enable verbose logging
  --resume           Resume from last checkpoint
  --auto-approve     Auto-approve all prompts (non-interactive)
  --help             Show help message
```

### Examples

```bash
# Interactive deployment
python scripts/deploy-azure.py

# Dry run with custom config
python scripts/deploy-azure.py --config my-config.yaml --dry-run

# Non-interactive deployment
python scripts/deploy-azure.py --auto-approve

# Resume with verbose logging
python scripts/deploy-azure.py --resume --verbose
```

## Deployment Steps

The deployment script executes the following steps:

1. **Check Prerequisites** - Verify Azure CLI, Docker, Python, etc.
2. **Create Resource Group** - Create Azure resource group
3. **Create Monitoring** - Set up Log Analytics and Application Insights
4. **Create Container Registry** - Create Azure Container Registry
5. **Create Key Vault** - Create Azure Key Vault for secrets
6. **Create Databases** - Create PostgreSQL and Redis
7. **Store Secrets** - Store all secrets in Key Vault
8. **Create Container Apps Environment** - Set up Container Apps environment
9. **Build and Push Images** - Build Docker images and push to ACR
10. **Deploy Infrastructure Services** - Deploy RabbitMQ and Qdrant
11. **Deploy Application Services** - Deploy all 5 application services
12. **Run Migrations** - Run database migrations
13. **Verify Deployment** - Verify all services are running
14. **Create Summary** - Generate deployment summary file

## Module Structure

```
scripts/azure/
├── README.md                    # This file
├── config.template.yaml         # Configuration template
├── utils.py                     # Utility functions
├── prerequisites.py             # Prerequisites checker
├── azure_resources.py           # Azure resource management
├── docker_builder.py            # Docker image building
├── container_apps.py            # Container Apps deployment
└── deployer.py                  # Main deployment orchestrator
```

### Module Descriptions

- **utils.py** - Common utilities (logging, colors, command execution, etc.)
- **prerequisites.py** - Checks all prerequisites (Azure CLI, Docker, login status)
- **azure_resources.py** - Creates Azure resources (RG, ACR, Key Vault, databases)
- **docker_builder.py** - Builds and pushes Docker images to ACR
- **container_apps.py** - Deploys applications to Azure Container Apps
- **deployer.py** - Main orchestrator that coordinates all modules

## State Management

The deployment script saves its state to `.azure-deployment-state.json` after each successful step. This allows you to resume deployment if it fails.

### State File Structure

```json
{
  "completed_steps": [
    "create_resource_group",
    "create_container_registry",
    "create_key_vault"
  ],
  "created_resources": {
    "resource_group": {
      "name": "draftgenie-rg",
      "location": "eastus"
    },
    "container_registry": {
      "name": "draftgenieacr",
      "login_server": "draftgenieacr.azurecr.io"
    }
  },
  "last_updated": "2024-01-15T10:30:00"
}
```

### Resuming Deployment

```bash
# Resume from last checkpoint
python scripts/deploy-azure.py --resume

# The script will:
# 1. Load the state file
# 2. Skip completed steps
# 3. Continue from the last failed step
```

## Logging

All deployment operations are logged to `azure-deployment.log`.

```bash
# View logs in real-time
tail -f azure-deployment.log

# Search for errors
grep ERROR azure-deployment.log
```

## Output Files

After successful deployment, the following files are created:

- **azure-deployment-summary.md** - Deployment summary with URLs and connection info
- **azure-deployment.log** - Detailed deployment log
- **.azure-deployment-state.json** - Deployment state (for resume)

## Troubleshooting

### Common Issues

#### 1. Azure CLI Not Logged In

```bash
Error: Not logged in to Azure

Solution:
az login
```

#### 2. Docker Daemon Not Running

```bash
Error: Docker daemon not running

Solution:
Start Docker Desktop
```

#### 3. Resource Name Already Exists

```bash
Error: Container registry name already exists

Solution:
Change the registry name in config.yaml to a unique value
```

#### 4. Insufficient Permissions

```bash
Error: Authorization failed

Solution:
Ensure your Azure account has Contributor role on the subscription
```

#### 5. Quota Exceeded

```bash
Error: Quota exceeded for resource type

Solution:
Request quota increase or choose a different region
```

### Getting Help

1. **Check Logs**: Review `azure-deployment.log` for detailed error messages
2. **Dry Run**: Use `--dry-run` to preview deployment
3. **Verbose Mode**: Use `--verbose` for detailed output
4. **GitHub Issues**: https://github.com/tan-res-space/draft-genie/issues

## Cleanup

To delete all created resources:

```bash
# Delete the entire resource group (WARNING: This deletes everything!)
az group delete --name draftgenie-rg --yes --no-wait

# Or delete individual resources
az containerapp delete --name api-gateway --resource-group draftgenie-rg
az acr delete --name draftgenieacr --resource-group draftgenie-rg
```

## Cost Estimation

Estimated monthly costs for development environment:

- Container Apps: $30-50
- PostgreSQL (B1ms): $15-20
- Redis (Basic C0): $15-20
- Container Registry (Basic): $5
- Log Analytics: $5-10
- Key Vault: $1-2
- **Total: $93-143/month**

See `docs/deployment/azure-deployment-guide.md` for detailed cost breakdown.

## Security Best Practices

1. **Secrets Management**
   - All secrets stored in Azure Key Vault
   - Never commit secrets to Git
   - Use managed identities where possible

2. **Network Security**
   - Internal services use internal ingress
   - Only API Gateway is publicly accessible
   - Database firewall rules configured

3. **Access Control**
   - Use Azure RBAC for access management
   - Follow principle of least privilege
   - Enable audit logging

## Next Steps

After successful deployment:

1. **Verify Deployment**
   ```bash
   curl https://your-api-gateway-url/api/v1/health
   ```

2. **Set Up Custom Domain** (Optional)
   - Follow Azure Container Apps custom domain guide
   - Configure DNS records
   - Enable SSL certificate

3. **Configure Monitoring**
   - Set up alerts in Application Insights
   - Create custom dashboards
   - Configure log retention

4. **Set Up CI/CD**
   - Create GitHub Actions workflow
   - Automate deployments
   - Add automated testing

5. **Optimize Costs**
   - Review resource usage
   - Adjust scaling settings
   - Set up budget alerts

## Contributing

Found a bug or want to improve the deployment scripts?

1. Open an issue describing the problem
2. Submit a pull request with improvements
3. Follow the existing code style

## License

These deployment scripts are part of the DraftGenie project and follow the same license.

---

**Happy Deploying! 🚀**

For detailed deployment guide, see: `docs/deployment/azure-deployment-guide.md`

