# deploy-azure_v1.py - Quick Reference Card

## 🚀 Common Commands

```bash
# First deployment
python scripts/deploy-azure_v1.py

# Resume after failure
python scripts/deploy-azure_v1.py --resume

# Force specific step
python scripts/deploy-azure_v1.py --force-step create_databases

# Force all steps
python scripts/deploy-azure_v1.py --force-all

# Reset state
python scripts/deploy-azure_v1.py --reset-state

# Dry run
python scripts/deploy-azure_v1.py --dry-run

# Non-interactive (CI/CD)
python scripts/deploy-azure_v1.py --auto-approve
```

## 📋 Step Names (for --force-step)

| Step Name | Description |
|-----------|-------------|
| `check_prerequisites` | Validate Azure CLI, Docker, etc. |
| `create_resource_group` | Create Azure resource group |
| `create_monitoring` | Create Log Analytics + App Insights |
| `create_container_registry` | Create Azure Container Registry |
| `create_key_vault` | Create Azure Key Vault |
| `create_databases` | Create PostgreSQL + Redis |
| `store_secrets` | Store secrets in Key Vault |
| `create_container_apps_env` | Create Container Apps environment |
| `build_and_push_images` | Build and push Docker images |
| `deploy_infrastructure_services` | Deploy RabbitMQ + Qdrant |
| `deploy_application_services` | Deploy 5 application services |
| `configure_environment_variables` | Configure env vars for all services |
| `run_migrations` | Run database migrations |
| `verify_deployment` | Verify and test deployment |

## 🔍 State File Location

- **Default:** `.azure-deployment-state-v1.json`
- **Custom:** Set in `config.yaml` → `advanced.state_file`
- **Blob Storage:** Set `AZURE_STATE_STORAGE=blob` environment variable

## 📊 State File Structure

```json
{
  "version": "1.0",
  "last_updated": "2024-01-15T10:30:00",
  "steps": {
    "step_name": {
      "status": "completed|failed|skipped",
      "timestamp": "2024-01-15T10:30:00",
      "dependency_hash": "sha256_hash",
      "error": "error message if failed"
    }
  },
  "resources": { /* created resources */ }
}
```

## 🎯 When Steps Re-execute

A step re-executes when:
- ✅ Never run before
- ✅ Failed in previous run
- ✅ Dependencies changed (files or config)
- ✅ Forced via `--force-step` or `--force-all`

A step is skipped when:
- ✅ Completed successfully before
- ✅ Dependencies unchanged
- ✅ Not forced

## 🔧 Troubleshooting

### View state file
```bash
cat .azure-deployment-state-v1.json | jq
```

### Check specific step status
```bash
cat .azure-deployment-state-v1.json | jq '.steps.create_databases'
```

### View logs
```bash
tail -f azure-deployment-v1.log
```

### Reset and start fresh
```bash
python scripts/deploy-azure_v1.py --reset-state
python scripts/deploy-azure_v1.py
```

### Force rebuild images
```bash
python scripts/deploy-azure_v1.py --force-step build_and_push_images
```

## 🌐 State Storage Options

### Local File (Default)
```yaml
# config.yaml
advanced:
  state_storage: local
  state_file: .azure-deployment-state-v1.json
```

### Azure Blob Storage
```yaml
# config.yaml
advanced:
  state_storage: blob
  state_blob_account: mystorageaccount
  state_blob_container: deployment-state
  state_blob_name: azure-deployment-state.json
```

Or via environment variable:
```bash
export AZURE_STATE_STORAGE=blob
```

## 📝 Configuration Dependencies

Each step tracks specific config keys:

| Step | Config Dependencies |
|------|---------------------|
| `create_resource_group` | `azure.resource_group`, `azure.location` |
| `create_databases` | `postgresql.*`, `redis.*` |
| `build_and_push_images` | `docker.dockerfiles` |
| `deploy_application_services` | `services.*` |

**Tip:** Changing these config values will trigger step re-execution.

## 🔐 Security Notes

- State file contains resource IDs and metadata (no secrets)
- Secrets are stored in Azure Key Vault
- Connection strings in state file are redacted in logs
- Use `.gitignore` to exclude state file if it contains sensitive data

## 🚦 Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Deployment failed |
| `130` | Interrupted by user (Ctrl+C) |

## 💡 Best Practices

1. ✅ Commit state file to git for team collaboration
2. ✅ Use `--dry-run` before production deployments
3. ✅ Use blob storage for CI/CD pipelines
4. ✅ Review logs after each deployment
5. ✅ Test with `--force-step` before `--force-all`
6. ✅ Keep config.yaml in sync with desired state

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
- name: Deploy
  run: |
    python scripts/deploy-azure_v1.py \
      --auto-approve \
      --verbose
  env:
    AZURE_STATE_STORAGE: blob
```

### Azure DevOps
```yaml
- script: |
    python scripts/deploy-azure_v1.py \
      --auto-approve \
      --verbose
  env:
    AZURE_STATE_STORAGE: blob
  displayName: 'Deploy to Azure'
```

## 📚 Related Files

- **Main Script:** `scripts/deploy-azure_v1.py`
- **Documentation:** `scripts/DEPLOY_AZURE_V1_README.md`
- **Example State:** `scripts/azure-deployment-state-v1.example.json`
- **Config Template:** `scripts/azure/config.template.yaml`
- **Original Script:** `scripts/deploy-azure.py`

## 🆘 Getting Help

```bash
# Show help
python scripts/deploy-azure_v1.py --help

# Check version
head -n 100 scripts/deploy-azure_v1.py | grep "Version"

# View deployment guide
cat docs/deployment/azure-deployment-guide.md
```

---

**Version:** 1.0  
**Last Updated:** 2024-01-15  
**Maintainer:** DraftGenie Team

