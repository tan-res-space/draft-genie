#!/usr/bin/env python3
"""
Verify State Migration Script

This script verifies that the state file migration is working correctly.
It checks if an existing state file can be loaded and migrated to the new format.
"""

import sys
import json
import os
from pathlib import Path

def check_state_file(state_file_path):
    """Check and display state file information."""
    print(f"\n{'='*80}")
    print(f"Checking state file: {state_file_path}")
    print(f"{'='*80}\n")
    
    if not os.path.exists(state_file_path):
        print(f"❌ State file does not exist: {state_file_path}")
        return False
    
    try:
        with open(state_file_path, 'r') as f:
            state = json.load(f)
        
        print("✓ State file loaded successfully\n")
        
        # Check for required keys
        print("State Structure Check:")
        print("-" * 40)
        
        required_keys = ['steps', 'resources', 'version', 'last_updated']
        legacy_keys = ['completed_steps', 'created_resources']
        
        all_keys_present = True
        
        for key in required_keys:
            if key in state:
                print(f"  ✓ {key:20s} : Present")
            else:
                print(f"  ✗ {key:20s} : MISSING")
                all_keys_present = False
        
        print("\nLegacy Keys (for backward compatibility):")
        print("-" * 40)
        
        for key in legacy_keys:
            if key in state:
                print(f"  ✓ {key:20s} : Present")
            else:
                print(f"  ℹ {key:20s} : Not present (will be added)")
        
        # Display state summary
        print("\nState Summary:")
        print("-" * 40)
        print(f"  Version: {state.get('version', 'N/A')}")
        print(f"  Last Updated: {state.get('last_updated', 'N/A')}")
        print(f"  Steps Tracked: {len(state.get('steps', {}))}")
        print(f"  Resources Tracked: {len(state.get('resources', {}))}")
        print(f"  Legacy Completed Steps: {len(state.get('completed_steps', []))}")
        print(f"  Legacy Created Resources: {len(state.get('created_resources', {}))}")
        
        # Display steps if any
        if state.get('steps'):
            print("\nTracked Steps:")
            print("-" * 40)
            for step_name, step_data in state['steps'].items():
                status = step_data.get('status', 'unknown')
                timestamp = step_data.get('timestamp', 'N/A')
                print(f"  • {step_name:30s} : {status:10s} ({timestamp})")
        
        # Display legacy completed steps if any
        if state.get('completed_steps'):
            print("\nLegacy Completed Steps:")
            print("-" * 40)
            for step in state['completed_steps']:
                print(f"  • {step}")
        
        print("\n" + "="*80)
        
        if all_keys_present:
            print("✅ State file is in correct v1 format")
            return True
        else:
            print("⚠️  State file needs migration (will be done automatically)")
            return True
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse state file as JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading state file: {e}")
        return False


def test_migration():
    """Test the migration logic."""
    print(f"\n{'='*80}")
    print("Testing State Migration Logic")
    print(f"{'='*80}\n")
    
    # Add scripts to path
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir / 'azure'))
    
    try:
        # Import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "deploy_azure_v1", 
            script_dir / "deploy-azure_v1.py"
        )
        dav1 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dav1)
        
        print("✓ Successfully imported deploy_azure_v1 module\n")
        
        # Test migration with old format
        print("Testing migration of old format state...")
        old_format = {
            "completed_steps": ["step1", "step2"],
            "created_resources": {"resource1": "value1"}
        }
        
        # Create a StateManager instance (it will use _validate_and_migrate_state)
        import logging
        logger = logging.getLogger('test')
        logger.setLevel(logging.WARNING)
        
        # Create a temporary config
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(old_format, f)
            temp_file = f.name
        
        try:
            config = {
                'advanced': {
                    'state_file': temp_file,
                    'state_storage': 'local'
                }
            }
            
            sm = dav1.StateManager(config, logger)
            
            # Check if migration worked
            required_keys = ['steps', 'resources', 'version', 'last_updated']
            migration_success = all(key in sm.state for key in required_keys)
            
            if migration_success:
                print("✓ Migration successful!")
                print(f"  • Added 'steps' key: {len(sm.state['steps'])} steps")
                print(f"  • Added 'resources' key: {len(sm.state['resources'])} resources")
                print(f"  • Added 'version' key: {sm.state['version']}")
                print(f"  • Preserved 'completed_steps': {len(sm.state['completed_steps'])} steps")
                print(f"  • Preserved 'created_resources': {len(sm.state['created_resources'])} resources")
            else:
                print("✗ Migration failed!")
                print(f"  State keys: {list(sm.state.keys())}")
                return False
                
        finally:
            os.unlink(temp_file)
        
        print("\n" + "="*80)
        print("✅ Migration logic is working correctly")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"❌ Error testing migration: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("\n" + "="*80)
    print("State Migration Verification Tool")
    print("="*80)
    
    # Check for state files
    state_files = [
        '.azure-deployment-state.json',
        '.azure-deployment-state-v1.json'
    ]
    
    found_files = []
    for state_file in state_files:
        if os.path.exists(state_file):
            found_files.append(state_file)
    
    if not found_files:
        print("\nℹ️  No state files found. This is normal for a fresh deployment.")
        print("   State file will be created on first deployment run.")
    else:
        print(f"\nFound {len(found_files)} state file(s):")
        for f in found_files:
            print(f"  • {f}")
    
    # Check each found file
    results = []
    for state_file in found_files:
        result = check_state_file(state_file)
        results.append((state_file, result))
    
    # Test migration logic
    migration_ok = test_migration()
    
    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    
    if found_files:
        print("\nState Files:")
        for state_file, result in results:
            status = "✅ OK" if result else "❌ ERROR"
            print(f"  {status} : {state_file}")
    
    print(f"\nMigration Logic: {'✅ OK' if migration_ok else '❌ ERROR'}")
    
    print("\n" + "="*80)
    
    if migration_ok and all(r for _, r in results):
        print("✅ All checks passed! The deployment script is ready to use.")
        print("\nYou can now run:")
        print("  python scripts/deploy-azure_v1.py --config scripts/azure/config.yaml")
        return 0
    else:
        print("⚠️  Some checks failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

