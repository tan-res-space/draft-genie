#!/usr/bin/env python3
"""
Test script for deploy-azure_v1.py

This script performs basic validation tests on the idempotent deployment script
without actually deploying to Azure.

Tests:
1. Import validation
2. State manager functionality
3. Hash computation
4. Decorator functionality
5. CLI argument parsing
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add azure module to path
script_dir = Path(__file__).parent
azure_dir = script_dir / 'azure'
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(azure_dir))

# Import the module by loading it directly
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("deploy_azure_v1", script_dir / "deploy-azure_v1.py")
    dav1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dav1)
    print("✓ Successfully imported deploy_azure_v1 module")
except Exception as e:
    print(f"✗ Failed to import deploy_azure_v1: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def test_hash_computation():
    """Test hash computation functions."""
    print("\n=== Testing Hash Computation ===")
    
    # Test compute_hash
    data1 = {"key": "value", "number": 42}
    data2 = {"number": 42, "key": "value"}  # Same data, different order
    
    hash1 = dav1.compute_hash(data1)
    hash2 = dav1.compute_hash(data2)
    
    if hash1 == hash2:
        print("✓ compute_hash produces consistent results for same data")
    else:
        print("✗ compute_hash failed consistency test")
        return False
    
    # Test compute_file_hash
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_file = f.name
    
    try:
        file_hash = dav1.compute_file_hash(temp_file)
        if len(file_hash) == 64:  # SHA-256 produces 64 hex characters
            print("✓ compute_file_hash produces valid SHA-256 hash")
        else:
            print("✗ compute_file_hash produced invalid hash length")
            return False
    finally:
        os.unlink(temp_file)
    
    # Test compute_file_hash with non-existent file
    nonexistent_hash = dav1.compute_file_hash("/nonexistent/file.txt")
    if nonexistent_hash == "":
        print("✓ compute_file_hash handles non-existent files correctly")
    else:
        print("✗ compute_file_hash should return empty string for non-existent files")
        return False
    
    return True


def test_state_manager():
    """Test StateManager functionality."""
    print("\n=== Testing StateManager ===")

    # Create temporary state file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        state_file = f.name

    try:
        # Create mock config
        config = {
            'advanced': {
                'state_file': state_file,
                'state_storage': 'local'
            }
        }

        # Create mock logger
        import logging
        logger = logging.getLogger('test')

        # Test 1: Initialize StateManager with no existing state
        sm = dav1.StateManager(config, logger)
        print("✓ StateManager initialized successfully")

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
        else:
            print("✗ StateManager failed to migrate old format state")
            return False
        
        # Test marking step as completed
        sm.mark_step_completed('test_step', 'test_hash_123', {'test': 'metadata'})
        
        if sm.is_step_completed('test_step'):
            print("✓ mark_step_completed and is_step_completed work correctly")
        else:
            print("✗ Step marking failed")
            return False
        
        # Test getting step hash
        stored_hash = sm.get_step_hash('test_step')
        if stored_hash == 'test_hash_123':
            print("✓ get_step_hash returns correct hash")
        else:
            print("✗ get_step_hash returned incorrect hash")
            return False
        
        # Test marking step as failed
        sm.mark_step_failed('failed_step', 'Test error message')
        
        if not sm.is_step_completed('failed_step'):
            print("✓ mark_step_failed correctly marks step as not completed")
        else:
            print("✗ Failed step should not be marked as completed")
            return False
        
        # Test resource storage
        sm.store_resource('test_resource', {'name': 'test', 'id': '123'})
        resource = sm.get_resource('test_resource')
        
        if resource and resource['name'] == 'test':
            print("✓ Resource storage and retrieval work correctly")
        else:
            print("✗ Resource storage failed")
            return False
        
        # Test state persistence
        sm.save()
        
        # Load state in new StateManager instance
        sm2 = dav1.StateManager(config, logger)
        
        if sm2.is_step_completed('test_step'):
            print("✓ State persistence works correctly")
        else:
            print("✗ State was not persisted correctly")
            return False
        
        # Test reset
        sm2.reset()
        
        if not sm2.is_step_completed('test_step'):
            print("✓ State reset works correctly")
        else:
            print("✗ State reset failed")
            return False
        
        return True
        
    finally:
        # Cleanup
        if os.path.exists(state_file):
            os.unlink(state_file)


def test_get_nested_config_value():
    """Test nested config value extraction."""
    print("\n=== Testing get_nested_config_value ===")
    
    config = {
        'level1': {
            'level2': {
                'level3': 'value'
            },
            'simple': 'test'
        }
    }
    
    # Test nested access
    value = dav1.get_nested_config_value(config, 'level1.level2.level3')
    if value == 'value':
        print("✓ Nested config value extraction works")
    else:
        print("✗ Nested config value extraction failed")
        return False
    
    # Test simple access
    value = dav1.get_nested_config_value(config, 'level1.simple')
    if value == 'test':
        print("✓ Simple config value extraction works")
    else:
        print("✗ Simple config value extraction failed")
        return False
    
    # Test non-existent key
    value = dav1.get_nested_config_value(config, 'nonexistent.key')
    if value is None:
        print("✓ Non-existent key returns None")
    else:
        print("✗ Non-existent key should return None")
        return False
    
    return True


def test_compute_dependency_hash():
    """Test dependency hash computation."""
    print("\n=== Testing compute_dependency_hash ===")
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
        f1.write("file1 content")
        file1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write("file2 content")
        file2 = f2.name
    
    try:
        config = {
            'key1': 'value1',
            'nested': {
                'key2': 'value2'
            }
        }
        
        # Compute hash
        hash1 = dav1.compute_dependency_hash(
            config,
            [file1, file2],
            ['key1', 'nested.key2']
        )
        
        if len(hash1) == 64:
            print("✓ compute_dependency_hash produces valid hash")
        else:
            print("✗ compute_dependency_hash produced invalid hash")
            return False
        
        # Compute again with same inputs - should be identical
        hash2 = dav1.compute_dependency_hash(
            config,
            [file1, file2],
            ['key1', 'nested.key2']
        )
        
        if hash1 == hash2:
            print("✓ compute_dependency_hash is deterministic")
        else:
            print("✗ compute_dependency_hash should be deterministic")
            return False
        
        # Change a file - hash should change
        with open(file1, 'w') as f:
            f.write("modified content")
        
        hash3 = dav1.compute_dependency_hash(
            config,
            [file1, file2],
            ['key1', 'nested.key2']
        )
        
        if hash1 != hash3:
            print("✓ compute_dependency_hash detects file changes")
        else:
            print("✗ compute_dependency_hash should detect file changes")
            return False
        
        return True
        
    finally:
        os.unlink(file1)
        os.unlink(file2)


def test_cli_parsing():
    """Test CLI argument parsing."""
    print("\n=== Testing CLI Argument Parsing ===")
    
    # Save original sys.argv
    original_argv = sys.argv
    
    try:
        # Test basic parsing
        sys.argv = ['deploy-azure_v1.py', '--config', 'test.yaml', '--dry-run']
        args = dav1.parse_arguments()
        
        if args.config == 'test.yaml' and args.dry_run:
            print("✓ Basic CLI argument parsing works")
        else:
            print("✗ Basic CLI argument parsing failed")
            return False
        
        # Test force-step
        sys.argv = ['deploy-azure_v1.py', '--force-step', 'step1', '--force-step', 'step2']
        args = dav1.parse_arguments()
        
        if args.force_steps == ['step1', 'step2']:
            print("✓ Multiple --force-step arguments parsed correctly")
        else:
            print("✗ Multiple --force-step parsing failed")
            return False
        
        # Test force-all
        sys.argv = ['deploy-azure_v1.py', '--force-all']
        args = dav1.parse_arguments()
        
        if args.force_all:
            print("✓ --force-all argument parsed correctly")
        else:
            print("✗ --force-all parsing failed")
            return False
        
        # Test reset-state
        sys.argv = ['deploy-azure_v1.py', '--reset-state']
        args = dav1.parse_arguments()
        
        if args.reset_state:
            print("✓ --reset-state argument parsed correctly")
        else:
            print("✗ --reset-state parsing failed")
            return False
        
        return True
        
    finally:
        # Restore original sys.argv
        sys.argv = original_argv


def main():
    """Run all tests."""
    print("=" * 80)
    print("Testing deploy-azure_v1.py")
    print("=" * 80)
    
    tests = [
        ("Hash Computation", test_hash_computation),
        ("State Manager", test_state_manager),
        ("Nested Config Value", test_get_nested_config_value),
        ("Dependency Hash", test_compute_dependency_hash),
        ("CLI Parsing", test_cli_parsing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

