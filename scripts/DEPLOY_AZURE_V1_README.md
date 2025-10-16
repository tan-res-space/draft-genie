# DraftGenie Azure Deployment Script v1 - Idempotent & Stateful

## Overview

`deploy-azure_v1.py` is an enhanced, production-ready deployment orchestration script for deploying DraftGenie to Microsoft Azure. It extends the original `deploy-azure.py` with **idempotent execution**, **stateful tracking**, and **intelligent change detection**.

### Key Features

✅ **Idempotent** - Safe to run multiple times; only executes what's needed  
✅ **Stateful** - Tracks completion status, timestamps, and dependency hashes  
✅ **Change Detection** - Re-executes steps only when dependencies change  
✅ **Error Recovery** - Preserves state on failure for easy resume  
✅ **Flexible State Storage** - Local file (default) or Azure Blob Storage (configurable)  
✅ **Force Execution** - Override idempotency for specific steps or all steps  
✅ **Comprehensive Logging** - Detailed logs for debugging and audit trails

---

## Quick Start

### Basic Usage

```bash
# First-time deployment
python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml

# Re-run after changes (only executes changed steps)
python scripts/deploy-azure_v1.py

# Resume after failure
python scripts/deploy-azure_v1.py --resume

# Force re-execution of specific step
python scripts/deploy-azure_v1.py --force-step create_databases

# Force complete re-deployment
python scripts/deploy-azure_v1.py --force-all

# Reset state and start fresh
python scripts/deploy-azure_v1.py --reset-state
```

---

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to configuration file (default: `scripts/azure/config.yaml`) |
| `--dry-run` | Preview deployment without creating resources |
| `--verbose` | Enable verbose logging |
| `--resume` | Resume from last checkpoint |
| `--auto-approve` | Auto-approve all prompts (for CI/CD) |
| `--force-step STEP` | Force re-execution of specific step (can be used multiple times) |
| `--force-all` | Force re-execution of all steps, ignoring state |
| `--reset-state` | Clear state file and start fresh |
| `--help` | Show help message |

---

## How It Works

### State Management

The script maintains a state file (default: `.azure-deployment-state-v1.json`) that tracks:

```json
{
  "version": "1.0",
  "last_updated": "2024-01-15T10:30:00",
  "steps": {
    "create_databases": {
      "status": "completed",
      "timestamp": "2024-01-15T10:25:00",
      "dependency_hash": "a1b2c3d4...",
      "metadata": {}
    }
  },
  "resources": {
    "postgresql": {
      "server_name": "draftgenie-postgres",
      "connection_string": "..."
    }
  }
}
```

### Change Detection

Each deployment step tracks its dependencies:

1. **File Dependencies** - Dockerfiles, deployment scripts, templates
2. **Configuration Dependencies** - Relevant config values (SKUs, names, etc.)

Before executing a step, the script:
1. Computes a SHA-256 hash of all dependencies
2. Compares with the stored hash from the last successful run
3. **Skips** if completed and dependencies unchanged
4. **Re-executes** if never run, failed before, or dependencies changed

### Deployment Steps

The script orchestrates 14 deployment steps:

| Step | Name | Dependencies |
|------|------|--------------|
| 1 | `check_prerequisites` | `prerequisites.py` |
| 2 | `create_resource_group` | `azure_resources.py`, config: `azure.resource_group`, `azure.location` |
| 3 | `create_monitoring` | `azure_resources.py`, config: `monitoring.*` |
| 4 | `create_container_registry` | `azure_resources.py`, config: `container_registry.*` |
| 5 | `create_key_vault` | `azure_resources.py`, config: `key_vault.name` |
| 6 | `create_databases` | `azure_resources.py`, config: `postgresql.*`, `redis.*` |
| 7 | `store_secrets` | `azure_resources.py`, config: `secrets.gemini_api_key` |
| 8 | `create_container_apps_env` | `azure_resources.py`, config: `container_apps.*` |
| 9 | `build_and_push_images` | `docker_builder.py`, all Dockerfiles, config: `docker.*` |
| 10 | `deploy_infrastructure_services` | `container_apps.py`, config: `services.rabbitmq`, `services.qdrant` |
| 11 | `deploy_application_services` | `container_apps.py`, config: `services.*` |
| 12 | `configure_environment_variables` | `env_configurator.py` |
| 13 | `run_migrations` | config: `deployment.skip_migrations` |
| 14 | `verify_deployment` | - |

---

## State Storage Options

### Option 1: Local File Storage (Default)

**Pros:**
- ✅ Simple setup - no additional Azure resources required
- ✅ Fast access - no network latency
- ✅ Works offline during development
- ✅ Easy to inspect and debug (human-readable JSON)
- ✅ No additional costs

**Cons:**
- ❌ Not shared across machines/CI runners
- ❌ Can be lost if local environment is destroyed
- ❌ Not suitable for team collaboration without version control
- ❌ Manual sync required for multi-environment deployments

**Recommended for:**
- Local development and testing
- Single-user deployments
- CI/CD with persistent runners
- Quick iterations and debugging

**Configuration:**
```yaml
# config.yaml
advanced:
  state_storage: local
  state_file: .azure-deployment-state-v1.json
```

### Option 2: Azure Blob Storage (Optional)

**Pros:**
- ✅ Centralized state accessible from anywhere
- ✅ Shared across team members and CI/CD pipelines
- ✅ Durable and highly available
- ✅ Supports concurrent deployments with proper locking
- ✅ Audit trail via blob versioning

**Cons:**
- ❌ Requires Azure Storage Account (additional resource)
- ❌ Network dependency - slower than local file
- ❌ Additional cost (minimal - typically <$1/month)
- ❌ More complex setup and authentication
- ❌ Requires internet connectivity

**Recommended for:**
- Team environments with multiple deployers
- CI/CD pipelines with ephemeral runners
- Production deployments requiring audit trails
- Multi-region deployments

**Configuration:**
```yaml
# config.yaml
advanced:
  state_storage: blob
  state_blob_account: <storage-account-name>
  state_blob_container: deployment-state
  state_blob_name: azure-deployment-state.json
```

**Or via environment variable:**
```bash
export AZURE_STATE_STORAGE=blob
python scripts/deploy-azure_v1.py
```

**Note:** Azure Blob Storage backend is currently a placeholder and requires implementation. See the TODO comments in the `StateManager` class.

---

## Usage Examples

### Example 1: First-Time Deployment

```bash
# Create configuration
cp scripts/azure/config.template.yaml scripts/azure/config.yaml
# Edit config.yaml with your values

# Run deployment
python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml --verbose

# Output:
# ✓ Step 'check_prerequisites' completed
# ✓ Step 'create_resource_group' completed
# ✓ Step 'create_monitoring' completed
# ...
# 🎉 Deployment completed successfully!
```

### Example 2: Re-run After Configuration Change

```bash
# Edit config.yaml - change PostgreSQL SKU from Standard_B1ms to Standard_B2s
vim scripts/azure/config.yaml

# Re-run deployment
python scripts/deploy-azure_v1.py

# Output:
# ✓ Step 'check_prerequisites' already completed and dependencies unchanged - skipping
# ✓ Step 'create_resource_group' already completed and dependencies unchanged - skipping
# ✓ Step 'create_monitoring' already completed and dependencies unchanged - skipping
# ✓ Step 'create_container_registry' already completed and dependencies unchanged - skipping
# ✓ Step 'create_key_vault' already completed and dependencies unchanged - skipping
# ⚠ Step 'create_databases' dependencies changed - re-executing
# ✓ Step 'create_databases' completed
# ✓ Step 'store_secrets' already completed and dependencies unchanged - skipping
# ...
```

### Example 3: Resume After Failure

```bash
# Deployment fails at step 9 (build_and_push_images)
python scripts/deploy-azure_v1.py

# Output:
# ✓ Step 'check_prerequisites' completed
# ...
# ✓ Step 'create_container_apps_env' completed
# ✗ Step 'build_and_push_images' failed
# ❌ Deployment failed

# Fix the issue (e.g., Docker daemon not running)
# Re-run to resume
python scripts/deploy-azure_v1.py --resume

# Output:
# ✓ Step 'check_prerequisites' already completed and dependencies unchanged - skipping
# ...
# ✓ Step 'create_container_apps_env' already completed and dependencies unchanged - skipping
# ✓ Step 'build_and_push_images' completed  # Retries the failed step
# ✓ Step 'deploy_infrastructure_services' completed
# ...
```

### Example 4: Force Re-execution of Specific Step

```bash
# Force rebuild of Docker images
python scripts/deploy-azure_v1.py --force-step build_and_push_images

# Force re-creation of databases
python scripts/deploy-azure_v1.py --force-step create_databases

# Force multiple steps
python scripts/deploy-azure_v1.py \
  --force-step build_and_push_images \
  --force-step deploy_application_services
```

### Example 5: Complete Re-deployment

```bash
# Force re-execution of all steps
python scripts/deploy-azure_v1.py --force-all

# Or reset state and start fresh
python scripts/deploy-azure_v1.py --reset-state
python scripts/deploy-azure_v1.py
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy DraftGenie
        run: |
          python scripts/deploy-azure_v1.py \
            --config scripts/azure/config.yaml \
            --auto-approve \
            --verbose
        env:
          AZURE_STATE_STORAGE: blob  # Use blob storage for CI/CD
```

---

## Troubleshooting

### Issue: State file corrupted

```bash
# Reset state and start fresh
python scripts/deploy-azure_v1.py --reset-state
```

### Issue: Step keeps re-executing even though nothing changed

```bash
# Check the state file to see the stored hash
cat .azure-deployment-state-v1.json | jq '.steps.step_name'

# Force the step to complete
python scripts/deploy-azure_v1.py --force-step step_name
```

### Issue: Want to skip a step that keeps failing

The script doesn't support skipping steps (by design - all steps are required). However, you can:
1. Fix the underlying issue
2. Manually mark the step as completed in the state file (not recommended)
3. Use `--dry-run` to test without making changes

---

## Differences from Original Script

| Feature | `deploy-azure.py` | `deploy-azure_v1.py` |
|---------|-------------------|----------------------|
| Idempotency | ❌ No | ✅ Yes |
| Change Detection | ❌ No | ✅ Yes (SHA-256 hashing) |
| State Tracking | ⚠️ Basic | ✅ Comprehensive |
| Force Execution | ❌ No | ✅ Yes (`--force-step`, `--force-all`) |
| State Storage | 📁 Local file only | 📁 Local file + ☁️ Azure Blob (configurable) |
| Dependency Tracking | ❌ No | ✅ Yes (files + config) |
| Error Recovery | ⚠️ Basic | ✅ Enhanced |

---

## Best Practices

1. **Version Control State File** - Commit `.azure-deployment-state-v1.json` to git for team collaboration
2. **Use Blob Storage for CI/CD** - Set `AZURE_STATE_STORAGE=blob` in CI/CD pipelines
3. **Review State Before Force-All** - `--force-all` will re-create all resources
4. **Keep Config in Sync** - Ensure config.yaml matches your desired state
5. **Monitor Logs** - Check `azure-deployment-v1.log` for detailed execution logs
6. **Test with Dry-Run** - Use `--dry-run` to preview changes before execution

---

## Future Enhancements

- [ ] Implement Azure Blob Storage backend for state management
- [ ] Add state locking for concurrent deployments
- [ ] Support for rollback to previous state
- [ ] Parallel execution of independent steps
- [ ] Terraform/Bicep template integration
- [ ] Cost estimation before deployment
- [ ] Automated testing after each step

---

## Support

For issues or questions:
1. Check the logs: `azure-deployment-v1.log`
2. Inspect the state file: `.azure-deployment-state-v1.json`
3. Review the original deployment guide: `docs/deployment/azure-deployment-guide.md`
4. Open an issue in the repository


