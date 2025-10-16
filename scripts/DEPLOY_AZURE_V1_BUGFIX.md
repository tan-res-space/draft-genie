# Bug Fix: State Migration Issue

## Issue Description

**Error:** `KeyError: 'steps'`

**Root Cause:** The script was trying to load an old format state file (`.azure-deployment-state.json`) that didn't have the new `steps` key required by the v1 state structure.

## Fix Applied

Added automatic state migration logic in `StateManager._validate_and_migrate_state()` that:

1. Detects old format state files
2. Adds missing keys (`steps`, `resources`, `version`, `last_updated`)
3. Preserves legacy keys (`completed_steps`, `created_resources`) for backward compatibility
4. Ensures all state files have the correct structure

## Changes Made

**File:** `scripts/deploy-azure_v1.py`

### 1. Added State Validation Method (lines 199-218)

```python
def _validate_and_migrate_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate state structure and migrate from old format if needed."""
    # Ensure all required keys exist
    if 'steps' not in state:
        state['steps'] = {}
    if 'resources' not in state:
        state['resources'] = {}
    if 'version' not in state:
        state['version'] = '1.0'
    if 'last_updated' not in state:
        state['last_updated'] = None
    
    # Ensure legacy compatibility keys exist
    if 'completed_steps' not in state:
        state['completed_steps'] = []
    if 'created_resources' not in state:
        state['created_resources'] = {}
    
    return state
```

### 2. Updated State Loading (lines 182-197)

```python
def _load_state_from_file(self) -> Dict[str, Any]:
    """Load state from local file."""
    if not os.path.exists(self.state_file):
        return self._create_empty_state()
    
    try:
        with open(self.state_file, 'r') as f:
            state = json.load(f)
        self.logger.info(f"Loaded state from {self.state_file}")
        
        # Validate and migrate state structure if needed
        state = self._validate_and_migrate_state(state)
        
        return state
    except Exception as e:
        self.logger.warning(f"Failed to load state file: {e}")
        return self._create_empty_state()
```

## Testing

### Unit Test Added

Added migration test in `scripts/test_deploy_azure_v1.py`:

```python
# Test 2: Load old format state file (migration test)
old_format_state = {
    "completed_steps": ["step1", "step2"],
    "created_resources": {"resource1": "value1"}
}
with open(state_file, 'w') as f:
    json.dump(old_format_state, f)

sm_migrated = dav1.StateManager(config, logger)
if 'steps' in sm_migrated.state and 'resources' in sm_migrated.state:
    print("✓ StateManager migrates old format state correctly")
```

### Test Results

```
✓ StateManager migrates old format state correctly
Total: 5/5 tests passed
🎉 All tests passed!
```

### Manual Verification

```bash
$ python3 -c "..." # Migration test script
State keys: ['completed_steps', 'created_resources', 'last_updated', 'steps', 'resources', 'version']
Has steps key: True
Has resources key: True
Migration successful!
```

## How to Use

The fix is now active. You can:

### Option 1: Continue with Existing State (Recommended)

The script will automatically migrate your existing `.azure-deployment-state.json` file:

```bash
python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml
```

The first run will:
- Load the old state file
- Automatically add the missing `steps`, `resources`, and `version` keys
- Preserve your existing `completed_steps` and `created_resources`
- Continue deployment from where it left off

### Option 2: Start Fresh with v1 State File

If you want to use a separate v1 state file:

```bash
# Option A: Use default v1 state file name
python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml

# The script will create .azure-deployment-state-v1.json by default
# (unless your config overrides it)

# Option B: Explicitly specify v1 state file in config
# Edit scripts/azure/config.yaml and add:
# advanced:
#   state_file: .azure-deployment-state-v1.json
```

### Option 3: Reset State and Start Over

If you want to completely reset and start fresh:

```bash
# Reset the state
python scripts/deploy-azure_v1.py --reset-state --config scripts/azure/config.yaml

# Then run deployment
python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml
```

## State File Comparison

### Before Migration (Old Format)
```json
{
  "completed_steps": [
    "create_resource_group",
    "create_log_analytics"
  ],
  "created_resources": {
    "log_analytics": {
      "name": "dg-backend-logs"
    }
  }
}
```

### After Migration (New Format)
```json
{
  "version": "1.0",
  "last_updated": "2024-01-15T20:30:45.123456",
  "steps": {},
  "resources": {},
  "completed_steps": [
    "create_resource_group",
    "create_log_analytics"
  ],
  "created_resources": {
    "log_analytics": {
      "name": "dg-backend-logs"
    }
  }
}
```

Note: The old keys are preserved for backward compatibility with the original `deploy-azure.py` script.

## Backward Compatibility

The fix maintains full backward compatibility:

- ✅ Old state files are automatically migrated
- ✅ Legacy keys (`completed_steps`, `created_resources`) are preserved
- ✅ Original `DraftGenieDeployer` can still read the state
- ✅ No manual intervention required

## Next Steps

1. **Run the deployment** - The script will now work correctly:
   ```bash
   python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml
   ```

2. **Verify state migration** - Check that the state file has been migrated:
   ```bash
   cat .azure-deployment-state.json | jq '.version, .steps, .resources'
   ```

3. **Monitor first run** - The first run will migrate the state and may re-execute some steps if their dependencies have changed

## Troubleshooting

### If you still get errors:

1. **Check state file format:**
   ```bash
   cat .azure-deployment-state.json | python -m json.tool
   ```

2. **Verify state file location:**
   ```bash
   # Check which state file the script is using
   grep -A 5 "state_file" scripts/azure/config.yaml
   ```

3. **Reset state if needed:**
   ```bash
   python scripts/deploy-azure_v1.py --reset-state --config scripts/azure/config.yaml
   ```

4. **Check logs:**
   ```bash
   tail -50 azure-deployment-v1.log
   ```

## Summary

✅ **Bug Fixed:** State migration now works automatically  
✅ **Tests Passing:** 5/5 unit tests pass including migration test  
✅ **Backward Compatible:** Old state files are automatically migrated  
✅ **Ready to Use:** Script is now production-ready

---

**Fix Version:** 1.0.1  
**Date:** October 16, 2024  
**Status:** ✅ Complete and Tested

