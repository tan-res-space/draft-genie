# Migration Guide: deploy-azure.py → deploy-azure_v1.py

## Overview

This guide helps you migrate from the original `deploy-azure.py` to the new idempotent, stateful `deploy-azure_v1.py` script.

## Key Differences

### Architecture Changes

| Aspect | deploy-azure.py | deploy-azure_v1.py |
|--------|-----------------|-------------------|
| **Execution Model** | Sequential, always runs all steps | Idempotent, skips completed steps |
| **State Management** | Basic (completed_steps list) | Comprehensive (status, timestamps, hashes) |
| **Change Detection** | None | SHA-256 hashing of dependencies |
| **Error Recovery** | Resume from checkpoint | Resume + intelligent retry |
| **State Storage** | Local file only | Local file + Azure Blob (configurable) |
| **Force Execution** | Not supported | `--force-step`, `--force-all` |
| **State File** | `.azure-deployment-state.json` | `.azure-deployment-state-v1.json` |

### Command-Line Interface

#### New Options in v1

```bash
--force-step STEP    # Force re-execution of specific step
--force-all          # Force re-execution of all steps
--reset-state        # Clear state and start fresh
```

#### Unchanged Options

```bash
--config PATH        # Same
--dry-run           # Same
--verbose           # Same
--resume            # Same (enhanced behavior)
--auto-approve      # Same
```

## Migration Steps

### Step 1: Backup Existing State

```bash
# Backup your current state file
cp .azure-deployment-state.json .azure-deployment-state.json.backup

# Backup your config
cp scripts/azure/config.yaml scripts/azure/config.yaml.backup
```

### Step 2: Review Configuration

The configuration file format is **100% compatible**. No changes needed.

```bash
# Verify your config is valid
python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml --dry-run
```

### Step 3: Choose Migration Strategy

#### Option A: Fresh Deployment (Recommended for Testing)

Start with a clean state to test the new script:

```bash
# Run with new state file (doesn't affect old state)
python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml

# The script will create .azure-deployment-state-v1.json
# Your old .azure-deployment-state.json remains untouched
```

#### Option B: Import Existing State

Convert your existing state to the new format:

```bash
# Create a migration script
cat > migrate_state.py << 'EOF'
#!/usr/bin/env python3
import json

# Load old state
with open('.azure-deployment-state.json', 'r') as f:
    old_state = json.load(f)

# Convert to new format
new_state = {
    "version": "1.0",
    "last_updated": old_state.get('last_updated'),
    "steps": {},
    "resources": old_state.get('created_resources', {}),
    "completed_steps": old_state.get('completed_steps', []),
    "created_resources": old_state.get('created_resources', {})
}

# Convert completed steps to new format
for step in old_state.get('completed_steps', []):
    new_state['steps'][step] = {
        'status': 'completed',
        'timestamp': old_state.get('last_updated', ''),
        'dependency_hash': '',  # Will be recomputed on next run
        'metadata': {'migrated': True}
    }

# Save new state
with open('.azure-deployment-state-v1.json', 'w') as f:
    json.dump(new_state, f, indent=2)

print("✓ State migrated successfully")
print("  Old state: .azure-deployment-state.json")
print("  New state: .azure-deployment-state-v1.json")
EOF

chmod +x migrate_state.py
python migrate_state.py
```

#### Option C: Side-by-Side (Recommended for Production)

Keep both scripts available during transition:

```bash
# Use old script for existing deployments
python scripts/deploy-azure.py --config scripts/azure/config.yaml

# Use new script for new deployments
python scripts/deploy-azure_v1.py --config scripts/azure/config-new.yaml
```

### Step 4: Test the New Script

```bash
# Dry run to verify
python scripts/deploy-azure_v1.py --dry-run --verbose

# Run actual deployment
python scripts/deploy-azure_v1.py --verbose
```

### Step 5: Verify Deployment

```bash
# Check state file
cat .azure-deployment-state-v1.json | jq

# Verify all steps completed
cat .azure-deployment-state-v1.json | jq '.steps | to_entries | map(select(.value.status == "completed")) | length'

# Check logs
tail -100 azure-deployment-v1.log
```

## Behavioral Changes

### 1. Step Execution Logic

**Old Behavior (deploy-azure.py):**
```
Run step → Check if in completed_steps → Skip if present
```

**New Behavior (deploy-azure_v1.py):**
```
Run step → Check status AND dependency hash → Skip only if completed AND unchanged
```

**Impact:** Steps may re-execute if dependencies changed, even if previously completed.

### 2. State File Format

**Old Format:**
```json
{
  "completed_steps": ["step1", "step2"],
  "created_resources": {...},
  "last_updated": "2024-01-15T10:30:00"
}
```

**New Format:**
```json
{
  "version": "1.0",
  "last_updated": "2024-01-15T10:30:00",
  "steps": {
    "step1": {
      "status": "completed",
      "timestamp": "...",
      "dependency_hash": "...",
      "metadata": {}
    }
  },
  "resources": {...},
  "completed_steps": [...],  // Legacy compatibility
  "created_resources": {...}  // Legacy compatibility
}
```

**Impact:** New format is backward compatible (includes legacy fields).

### 3. Error Handling

**Old Behavior:**
- Step fails → Save state → Exit
- Resume → Continue from next step

**New Behavior:**
- Step fails → Mark as failed in state → Exit
- Resume → Retry failed step (not skip to next)

**Impact:** Failed steps are retried instead of skipped.

## Common Migration Scenarios

### Scenario 1: Existing Deployment, Want to Update Config

```bash
# Edit config
vim scripts/azure/config.yaml

# Run v1 script - it will detect changes and re-execute affected steps
python scripts/deploy-azure_v1.py
```

### Scenario 2: Deployment Failed Halfway, Want to Resume

```bash
# Old way
python scripts/deploy-azure.py --resume

# New way (same command, better behavior)
python scripts/deploy-azure_v1.py --resume
```

### Scenario 3: Want to Rebuild Docker Images Only

```bash
# Old way: Not possible without manual state editing

# New way
python scripts/deploy-azure_v1.py --force-step build_and_push_images
```

### Scenario 4: Complete Re-deployment

```bash
# Old way: Delete state file
rm .azure-deployment-state.json
python scripts/deploy-azure.py

# New way: Use --force-all or --reset-state
python scripts/deploy-azure_v1.py --force-all
# or
python scripts/deploy-azure_v1.py --reset-state
python scripts/deploy-azure_v1.py
```

## Rollback Plan

If you need to rollback to the old script:

```bash
# Restore old state file
cp .azure-deployment-state.json.backup .azure-deployment-state.json

# Use old script
python scripts/deploy-azure.py --resume
```

The old script is **not affected** by the new script's state file.

## CI/CD Migration

### Before (deploy-azure.py)

```yaml
# .github/workflows/deploy.yml
- name: Deploy to Azure
  run: |
    python scripts/deploy-azure.py \
      --config scripts/azure/config.yaml \
      --auto-approve
```

### After (deploy-azure_v1.py)

```yaml
# .github/workflows/deploy.yml
- name: Deploy to Azure
  run: |
    python scripts/deploy-azure_v1.py \
      --config scripts/azure/config.yaml \
      --auto-approve \
      --verbose
  env:
    AZURE_STATE_STORAGE: blob  # Optional: Use blob storage
```

**Key Changes:**
- Script name changed
- Consider using blob storage for CI/CD
- Add `--verbose` for better logs

## Troubleshooting Migration Issues

### Issue: "Step keeps re-executing even though nothing changed"

**Cause:** Dependency hash is empty (migrated state) or file paths changed.

**Solution:**
```bash
# Let it run once to compute hashes
python scripts/deploy-azure_v1.py

# Or force the step to complete
python scripts/deploy-azure_v1.py --force-step step_name
```

### Issue: "State file not found"

**Cause:** New script uses different state file name.

**Solution:**
```bash
# Either migrate state (see Step 3, Option B)
# Or start fresh
python scripts/deploy-azure_v1.py
```

### Issue: "Configuration validation failed"

**Cause:** Config format is the same, but validation is stricter.

**Solution:**
```bash
# Check config
python scripts/deploy-azure_v1.py --dry-run --verbose

# Fix validation errors in config.yaml
```

## Best Practices for Migration

1. ✅ **Test in Non-Production First**
   - Migrate dev/staging environments before production
   - Verify behavior matches expectations

2. ✅ **Keep Both Scripts During Transition**
   - Don't delete `deploy-azure.py` immediately
   - Run both in parallel for a few deployments

3. ✅ **Use Version Control**
   - Commit state files to git
   - Track changes over time

4. ✅ **Monitor First Few Runs**
   - Watch for unexpected re-executions
   - Verify dependency detection works correctly

5. ✅ **Document Your Migration**
   - Note any custom changes or workarounds
   - Share learnings with team

## Timeline Recommendation

| Week | Activity |
|------|----------|
| Week 1 | Test v1 in dev environment, verify behavior |
| Week 2 | Migrate staging environment, monitor closely |
| Week 3 | Migrate production with rollback plan ready |
| Week 4 | Deprecate old script, update documentation |

## Support

If you encounter issues during migration:

1. Check logs: `azure-deployment-v1.log`
2. Compare state files: `diff .azure-deployment-state.json .azure-deployment-state-v1.json`
3. Review this guide: `scripts/DEPLOY_AZURE_V1_MIGRATION_GUIDE.md`
4. Consult main documentation: `scripts/DEPLOY_AZURE_V1_README.md`
5. Open an issue with migration details

---

**Migration Guide Version:** 1.0  
**Last Updated:** 2024-01-15  
**Compatibility:** deploy-azure.py (all versions) → deploy-azure_v1.py

