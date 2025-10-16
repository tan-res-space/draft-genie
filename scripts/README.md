# DraftGenie Deployment Scripts

Automated deployment scripts for deploying DraftGenie to various cloud platforms.

## Overview

This directory contains production-ready deployment automation scripts that transform the manual deployment processes from the deployment guides into streamlined, automated experiences.

## Available Deployment Scripts

### 1. Azure Deployment

**Location:** `scripts/deploy-azure.py`  
**Documentation:** `scripts/azure/README.md`  
**Guide:** `docs/deployment/azure-deployment-guide.md`

Automated deployment to Microsoft Azure using:
- Azure Container Apps
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Container Registry
- Azure Key Vault
- Application Insights

**Quick Start:**
```bash
# Interactive deployment
python scripts/deploy-azure.py

# Or use the setup wizard
bash scripts/azure/setup.sh
```

**Features:**
- ✅ Fully automated deployment
- ✅ Interactive configuration wizard
- ✅ Resumable from checkpoints
- ✅ Dry run mode
- ✅ Comprehensive error handling
- ✅ State management
- ✅ Secrets management

**Estimated Time:** 30-45 minutes  
**Estimated Cost:** $93-143/month (development)

---

### 2. GCP Deployment (Coming Soon)

**Location:** `scripts/deploy-gcp.py` (planned)  
**Guide:** `docs/deployment/gcp-deployment-guide.md`

Automated deployment to Google Cloud Platform using:
- Cloud Run
- Cloud SQL
- Memorystore for Redis
- Artifact Registry
- Secret Manager
- Cloud Monitoring

**Status:** 🚧 In Development

---

### 3. Zoho Cloud Deployment (Coming Soon)

**Location:** `scripts/deploy-zoho.py` (planned)  
**Guide:** `docs/deployment/zoho-deployment-guide.md`

Automated deployment to Zoho Cloud using:
- Zoho Catalyst
- Render.com
- MongoDB Atlas
- Upstash Redis
- CloudAMQP

**Status:** 🚧 In Development

---

## Prerequisites

### Common Requirements

All deployment scripts require:

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **Docker**
   ```bash
   docker --version
   ```

4. **Google Gemini API Key**
   - Get from: https://makersuite.google.com/app/apikey

### Platform-Specific Requirements

#### Azure
- Azure CLI: `az --version`
- Azure account with active subscription
- Logged in: `az login`

#### GCP (Coming Soon)
- gcloud CLI: `gcloud --version`
- GCP account with billing enabled
- Logged in: `gcloud auth login`

#### Zoho (Coming Soon)
- Catalyst CLI: `zcatalyst --version`
- Zoho account
- Logged in: `zcatalyst login`

---

## Installation

### 1. Install Python Dependencies

**Option 1: Using Virtual Environment (Recommended)**

```bash
# Set up virtual environment and install all dependencies
bash scripts/setup-venv.sh

# Activate virtual environment
source scripts/venv/bin/activate
```

This approach:
- ✅ Isolates dependencies from system Python
- ✅ Prevents version conflicts
- ✅ Easy to recreate if needed
- ✅ Automatically excluded from git

**Option 2: Global Installation**

```bash
pip install -r scripts/requirements.txt
```

### 2. Install Platform CLI Tools

**Azure:**
```bash
# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Windows
# Download from https://aka.ms/installazurecliwindows
```

**GCP (Coming Soon):**
```bash
# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Download from https://cloud.google.com/sdk/docs/install
```

**Zoho (Coming Soon):**
```bash
npm install -g zcatalyst-cli
```

---

## Usage

### Azure Deployment

#### Option 1: Interactive Deployment (Recommended)

```bash
# Run setup wizard
bash scripts/azure/setup.sh

# Or run deployment directly
python scripts/deploy-azure.py
```

The script will guide you through:
1. Configuration setup
2. Prerequisites check
3. Resource creation
4. Docker image building
5. Service deployment
6. Verification

#### Option 2: Configuration File

```bash
# Copy template
cp scripts/azure/config.template.yaml scripts/azure/config.yaml

# Edit configuration
nano scripts/azure/config.yaml

# Run deployment
python scripts/deploy-azure.py --config scripts/azure/config.yaml
```

#### Option 3: Dry Run

```bash
# Preview deployment without creating resources
python scripts/deploy-azure.py --dry-run
```

#### Option 4: Resume from Checkpoint

```bash
# If deployment fails, resume from last successful step
python scripts/deploy-azure.py --resume
```

### Command Line Options

```bash
python scripts/deploy-azure.py [OPTIONS]

Options:
  --config PATH       Path to configuration file
  --dry-run          Preview without creating resources
  --verbose          Enable verbose logging
  --resume           Resume from last checkpoint
  --auto-approve     Skip confirmation prompts
  --help             Show help message
```

---

## Directory Structure

```
scripts/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── deploy-azure.py              # Azure deployment script
│
├── docker/                      # Docker build scripts (NEW!)
│   ├── README.md               # Docker scripts documentation
│   ├── QUICK_REFERENCE.md      # Quick reference guide
│   ├── IMPLEMENTATION_SUMMARY.md # Implementation details
│   ├── build-all-services.sh   # Build all services
│   ├── build-push-api-gateway.sh        # API Gateway
│   ├── build-push-speaker-service.sh    # Speaker Service
│   ├── build-push-draft-service.sh      # Draft Service
│   ├── build-push-rag-service.sh        # RAG Service
│   └── build-push-evaluation-service.sh # Evaluation Service
│
├── azure/                       # Azure deployment modules
│   ├── README.md               # Azure-specific documentation
│   ├── setup.sh                # Quick setup script
│   ├── cleanup.py              # Resource cleanup script
│   ├── config.template.yaml    # Configuration template
│   ├── config.example.yaml     # Example configuration
│   ├── utils.py                # Utility functions
│   ├── prerequisites.py        # Prerequisites checker
│   ├── azure_resources.py      # Azure resource management
│   ├── docker_builder.py       # Docker image building
│   ├── container_apps.py       # Container Apps deployment
│   └── deployer.py             # Main deployment orchestrator
│
├── gcp/                        # GCP deployment (coming soon)
│   └── ...
│
└── zoho/                       # Zoho deployment (coming soon)
    └── ...
```

---

## Docker Build Scripts

### Individual Service Scripts

Build and push Docker images for individual services:

```bash
# Build and push a single service
./scripts/docker/build-push-api-gateway.sh
./scripts/docker/build-push-speaker-service.sh
./scripts/docker/build-push-draft-service.sh
./scripts/docker/build-push-rag-service.sh
./scripts/docker/build-push-evaluation-service.sh

# Build and push all services
./scripts/docker/build-all-services.sh
```

**Features:**
- ✅ Independent service builds
- ✅ Custom image tags
- ✅ Dry run mode
- ✅ Skip build/push options
- ✅ Parallel execution support
- ✅ Automatic registry login

**Quick Examples:**
```bash
# Build with custom tag
TAG=v1.2.3 ./scripts/docker/build-push-api-gateway.sh

# Build all services in parallel
PARALLEL=true ./scripts/docker/build-all-services.sh

# Dry run test
DRY_RUN=true ./scripts/docker/build-push-draft-service.sh
```

**Documentation:**
- Full guide: `scripts/docker/README.md`
- Quick reference: `scripts/docker/QUICK_REFERENCE.md`

---

## Features

### Modular Design

Each deployment script is broken down into logical modules:

- **Prerequisites Checker** - Validates all requirements
- **Resource Manager** - Creates cloud resources
- **Docker Builder** - Builds and pushes images (Python or Shell scripts)
- **Service Deployer** - Deploys applications
- **Orchestrator** - Coordinates all modules

### State Management

Deployment state is saved after each successful step:

```json
{
  "completed_steps": [
    "create_resource_group",
    "create_container_registry",
    "create_key_vault"
  ],
  "created_resources": {
    "resource_group": {...},
    "container_registry": {...}
  },
  "last_updated": "2024-01-15T10:30:00"
}
```

Resume deployment if it fails:
```bash
python scripts/deploy-azure.py --resume
```

### Error Handling

- Comprehensive error messages
- Detailed logging to file
- Graceful failure handling
- Rollback capability (optional)

### Secrets Management

- Secure password generation
- Secrets stored in platform secret managers
- Never logged or displayed
- Auto-generated if not provided

---

## Output Files

After deployment, the following files are created:

- **{platform}-deployment-summary.md** - Deployment summary with URLs
- **{platform}-deployment.log** - Detailed deployment log
- **.{platform}-deployment-state.json** - Deployment state

---

## Cleanup

### Azure

```bash
# Delete all resources
python scripts/azure/cleanup.py --config scripts/azure/config.yaml

# Or delete resource group directly
az group delete --name draftgenie-rg --yes
```

### GCP (Coming Soon)

```bash
python scripts/gcp/cleanup.py --config scripts/gcp/config.yaml
```

### Zoho (Coming Soon)

```bash
python scripts/zoho/cleanup.py --config scripts/zoho/config.yaml
```

---

## Troubleshooting

### Common Issues

#### 1. Prerequisites Not Met

```bash
Error: Azure CLI not found

Solution:
Install Azure CLI: brew install azure-cli
```

#### 2. Not Logged In

```bash
Error: Not logged in to Azure

Solution:
az login
```

#### 3. Docker Daemon Not Running

```bash
Error: Docker daemon not running

Solution:
Start Docker Desktop
```

#### 4. Configuration Invalid

```bash
Error: Gemini API key is required

Solution:
Add your Gemini API key to config.yaml
```

### Getting Help

1. **Check Logs**: Review `{platform}-deployment.log`
2. **Dry Run**: Use `--dry-run` to preview
3. **Verbose Mode**: Use `--verbose` for detailed output
4. **GitHub Issues**: https://github.com/tan-res-space/draft-genie/issues

---

## Development

### Adding a New Platform

To add deployment automation for a new platform:

1. Create platform directory: `scripts/{platform}/`
2. Create modules:
   - `utils.py` - Utility functions
   - `prerequisites.py` - Prerequisites checker
   - `resources.py` - Resource management
   - `deployer.py` - Main orchestrator
3. Create main script: `scripts/deploy-{platform}.py`
4. Create configuration template
5. Create README with platform-specific instructions
6. Update this README

### Testing

```bash
# Test with dry run
python scripts/deploy-azure.py --dry-run --verbose

# Test prerequisites
python -c "from scripts.azure.prerequisites import *; check_prerequisites()"
```

---

## Contributing

Contributions are welcome! Please:

1. Follow the existing code structure
2. Add comprehensive error handling
3. Include logging for all operations
4. Update documentation
5. Test with dry run mode

---

## License

These deployment scripts are part of the DraftGenie project and follow the same license.

---

## Support

- **Documentation**: See platform-specific READMEs
- **Deployment Guides**: See `docs/deployment/`
- **Issues**: https://github.com/tan-res-space/draft-genie/issues
- **Discussions**: https://github.com/tan-res-space/draft-genie/discussions

---

**Happy Deploying! 🚀**

