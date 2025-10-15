#!/usr/bin/env python3
"""
Verification script for Azure deployment automation.

This script verifies that all modules are working correctly.
"""

import sys
import os
from pathlib import Path

# Add azure module to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        import utils
        print("✓ utils.py")
    except Exception as e:
        print(f"✗ utils.py: {e}")
        return False
    
    try:
        import prerequisites
        print("✓ prerequisites.py")
    except Exception as e:
        print(f"✗ prerequisites.py: {e}")
        return False
    
    try:
        import azure_resources
        print("✓ azure_resources.py")
    except Exception as e:
        print(f"✗ azure_resources.py: {e}")
        return False
    
    try:
        import docker_builder
        print("✓ docker_builder.py")
    except Exception as e:
        print(f"✗ docker_builder.py: {e}")
        return False
    
    try:
        import container_apps
        print("✓ container_apps.py")
    except Exception as e:
        print(f"✗ container_apps.py: {e}")
        return False
    
    try:
        import deployer
        print("✓ deployer.py")
    except Exception as e:
        print(f"✗ deployer.py: {e}")
        return False
    
    return True


def test_config_files():
    """Test that configuration files exist."""
    print("\nTesting configuration files...")
    
    files = [
        'config.template.yaml',
        'config.example.yaml'
    ]
    
    all_exist = True
    for file in files:
        path = script_dir / file
        if path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} not found")
            all_exist = False
    
    return all_exist


def test_scripts():
    """Test that scripts exist and are executable."""
    print("\nTesting scripts...")
    
    scripts = [
        ('setup.sh', True),
        ('cleanup.py', True),
        ('verify.py', True)
    ]
    
    all_ok = True
    for script, should_be_executable in scripts:
        path = script_dir / script
        if not path.exists():
            print(f"✗ {script} not found")
            all_ok = False
            continue
        
        if should_be_executable and not os.access(path, os.X_OK):
            print(f"⚠ {script} exists but not executable")
        else:
            print(f"✓ {script}")
    
    return all_ok


def test_main_script():
    """Test that main deployment script exists."""
    print("\nTesting main deployment script...")
    
    main_script = script_dir.parent / 'deploy-azure.py'
    
    if not main_script.exists():
        print("✗ deploy-azure.py not found")
        return False
    
    if not os.access(main_script, os.X_OK):
        print("⚠ deploy-azure.py exists but not executable")
    else:
        print("✓ deploy-azure.py")
    
    return True


def test_documentation():
    """Test that documentation exists."""
    print("\nTesting documentation...")
    
    docs = [
        'README.md',
        'DEPLOYMENT_AUTOMATION_SUMMARY.md'
    ]
    
    all_exist = True
    for doc in docs:
        path = script_dir / doc
        if path.exists():
            print(f"✓ {doc}")
        else:
            print(f"✗ {doc} not found")
            all_exist = False
    
    return all_exist


def test_utils_functions():
    """Test utility functions."""
    print("\nTesting utility functions...")
    
    try:
        from utils import (
            generate_password, generate_secret,
            validate_resource_name, get_project_root
        )
        
        # Test password generation
        password = generate_password(32)
        if len(password) == 32:
            print("✓ generate_password()")
        else:
            print("✗ generate_password() - wrong length")
            return False
        
        # Test secret generation
        secret = generate_secret(32)
        if len(secret) > 0:
            print("✓ generate_secret()")
        else:
            print("✗ generate_secret() - empty")
            return False
        
        # Test resource name validation
        if validate_resource_name('test123', 'container_registry'):
            print("✓ validate_resource_name()")
        else:
            print("✗ validate_resource_name()")
            return False
        
        # Test project root
        root = get_project_root()
        if root.exists():
            print("✓ get_project_root()")
        else:
            print("✗ get_project_root()")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Utility functions test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Azure Deployment Automation - Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("Configuration Files", test_config_files()))
    results.append(("Scripts", test_scripts()))
    results.append(("Main Script", test_main_script()))
    results.append(("Documentation", test_documentation()))
    results.append(("Utility Functions", test_utils_functions()))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Total: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

