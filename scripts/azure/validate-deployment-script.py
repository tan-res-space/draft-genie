#!/usr/bin/env python3
"""
Validation script for the updated deployment script.

This script verifies that all the critical fixes have been properly applied
to the deployment script without actually running a deployment.

Usage:
    python scripts/azure/validate-deployment-script.py
"""

import os
import sys
import re
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

def print_header(msg):
    print(f"\n{'=' * 80}")
    print(f"{BLUE}{msg}{RESET}")
    print('=' * 80)

def check_file_exists(filepath):
    """Check if a file exists."""
    if Path(filepath).exists():
        print_success(f"File exists: {filepath}")
        return True
    else:
        print_error(f"File not found: {filepath}")
        return False

def check_code_contains(filepath, pattern, description):
    """Check if a file contains a specific pattern."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE):
                print_success(f"{description}")
                return True
            else:
                print_error(f"{description} - NOT FOUND")
                return False
    except Exception as e:
        print_error(f"Error reading {filepath}: {str(e)}")
        return False

def validate_docker_builder():
    """Validate docker_builder.py has all required fixes."""
    print_header("Validating docker_builder.py")
    
    filepath = "scripts/azure/docker_builder.py"
    checks_passed = 0
    total_checks = 5
    
    # Check 1: File exists
    if check_file_exists(filepath):
        checks_passed += 1
    
    # Check 2: AMD64 platform flag
    if check_code_contains(
        filepath,
        r"--platform.*linux/amd64",
        "AMD64 platform flag in build command"
    ):
        checks_passed += 1
    
    # Check 3: Docker Desktop PATH fix
    if check_code_contains(
        filepath,
        r"def _ensure_docker_desktop_in_path",
        "Docker Desktop PATH fix method exists"
    ):
        checks_passed += 1
    
    # Check 4: Enhanced logging in build_image
    if check_code_contains(
        filepath,
        r"print_info.*Platform:.*linux/amd64",
        "Enhanced logging for platform in build_image"
    ):
        checks_passed += 1
    
    # Check 5: Comprehensive error handling in build_and_push_all
    if check_code_contains(
        filepath,
        r"try:.*success, image_name = self\.build_and_push_service",
        "Try-catch error handling in build_and_push_all"
    ):
        checks_passed += 1
    
    print_info(f"\nDocker Builder Validation: {checks_passed}/{total_checks} checks passed")
    return checks_passed == total_checks

def validate_deployer():
    """Validate deployer.py has all required fixes."""
    print_header("Validating deployer.py")
    
    filepath = "scripts/azure/deployer.py"
    checks_passed = 0
    total_checks = 5
    
    # Check 1: File exists
    if check_file_exists(filepath):
        checks_passed += 1
    
    # Check 2: run_command import
    if check_code_contains(
        filepath,
        r"from utils import.*run_command",
        "run_command imported for service testing"
    ):
        checks_passed += 1
    
    # Check 3: Service testing in verify_deployment
    if check_code_contains(
        filepath,
        r"services_to_test = \[",
        "Service testing list in verify_deployment"
    ):
        checks_passed += 1
    
    # Check 4: Health check testing
    if check_code_contains(
        filepath,
        r"health_url.*api/v1/health",
        "Health endpoint testing"
    ):
        checks_passed += 1
    
    # Check 5: Service status checking
    if check_code_contains(
        filepath,
        r"az.*containerapp.*show",
        "Azure CLI service status checking"
    ):
        checks_passed += 1
    
    print_info(f"\nDeployer Validation: {checks_passed}/{total_checks} checks passed")
    return checks_passed == total_checks

def validate_documentation():
    """Validate documentation files exist."""
    print_header("Validating Documentation")
    
    docs = [
        "scripts/azure/DEPLOYMENT_SCRIPT_UPDATES.md",
        "DEPLOYMENT_UPDATE_SUMMARY.md",
        "scripts/azure/QUICK_REFERENCE.md"
    ]
    
    checks_passed = 0
    for doc in docs:
        if check_file_exists(doc):
            checks_passed += 1
    
    print_info(f"\nDocumentation Validation: {checks_passed}/{len(docs)} files exist")
    return checks_passed == len(docs)

def validate_main_script():
    """Validate main deploy-azure.py script."""
    print_header("Validating deploy-azure.py")
    
    filepath = "scripts/deploy-azure.py"
    checks_passed = 0
    total_checks = 3
    
    # Check 1: File exists
    if check_file_exists(filepath):
        checks_passed += 1
    
    # Check 2: Imports DockerBuilder
    if check_code_contains(
        filepath,
        r"from docker_builder import DockerBuilder",
        "DockerBuilder import exists"
    ):
        checks_passed += 1
    
    # Check 3: Imports DraftGenieDeployer
    if check_code_contains(
        filepath,
        r"from deployer import DraftGenieDeployer",
        "DraftGenieDeployer import exists"
    ):
        checks_passed += 1
    
    print_info(f"\nMain Script Validation: {checks_passed}/{total_checks} checks passed")
    return checks_passed == total_checks

def check_python_syntax():
    """Check Python syntax of updated files."""
    print_header("Checking Python Syntax")
    
    files_to_check = [
        "scripts/deploy-azure.py",
        "scripts/azure/docker_builder.py",
        "scripts/azure/deployer.py"
    ]
    
    all_valid = True
    for filepath in files_to_check:
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), filepath, 'exec')
            print_success(f"Valid Python syntax: {filepath}")
        except SyntaxError as e:
            print_error(f"Syntax error in {filepath}: {str(e)}")
            all_valid = False
        except Exception as e:
            print_error(f"Error checking {filepath}: {str(e)}")
            all_valid = False
    
    return all_valid

def main():
    """Run all validations."""
    print_header("Deployment Script Validation")
    print_info("Validating all updates to the deployment script...")
    
    results = {
        "Docker Builder": validate_docker_builder(),
        "Deployer": validate_deployer(),
        "Documentation": validate_documentation(),
        "Main Script": validate_main_script(),
        "Python Syntax": check_python_syntax()
    }
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for component, result in results.items():
        if result:
            print_success(f"{component}: PASSED")
        else:
            print_error(f"{component}: FAILED")
    
    print(f"\n{'=' * 80}")
    if passed == total:
        print_success(f"All validations passed! ({passed}/{total})")
        print_info("\n✅ The deployment script is ready to use!")
        print_info("\nNext steps:")
        print_info("  1. Review the changes: cat scripts/azure/DEPLOYMENT_SCRIPT_UPDATES.md")
        print_info("  2. Test with dry run: python scripts/deploy-azure.py --dry-run")
        print_info("  3. Run deployment: python scripts/deploy-azure.py --verbose")
        return 0
    else:
        print_error(f"Some validations failed ({passed}/{total})")
        print_warning("\n⚠ Please review the errors above and fix them before deploying.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

