#!/usr/bin/env python3
"""
DraftGenie Azure Cleanup Script

This script helps clean up Azure resources created by the deployment script.

Usage:
    python scripts/azure/cleanup.py [options]

Options:
    --config PATH       Path to configuration file
    --resource-group    Resource group name to delete
    --dry-run          Preview what will be deleted
    --force            Skip confirmation prompts
    --help             Show this help message
"""

import sys
import os
import argparse
from pathlib import Path

# Add azure module to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from utils import (
    setup_logging, load_config, print_header, print_success,
    print_error, print_warning, print_info, confirm_action,
    run_az_command
)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Clean up DraftGenie Azure resources',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--resource-group',
        type=str,
        help='Resource group name to delete'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what will be deleted without actually deleting'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    return parser.parse_args()


def list_resources_in_group(resource_group: str, logger) -> list:
    """
    List all resources in a resource group.
    
    Args:
        resource_group: Resource group name
        logger: Logger instance
        
    Returns:
        List of resource dictionaries
    """
    returncode, stdout, stderr = run_az_command(
        [
            'resource', 'list',
            '--resource-group', resource_group,
            '--output', 'json'
        ],
        check=False,
        logger=logger
    )
    
    if returncode == 0:
        import json
        return json.loads(stdout)
    
    return []


def delete_resource_group(resource_group: str, dry_run: bool, logger) -> bool:
    """
    Delete a resource group and all its resources.
    
    Args:
        resource_group: Resource group name
        dry_run: Dry run mode
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print_info(f"[DRY RUN] Would delete resource group: {resource_group}")
        return True
    
    print_info(f"Deleting resource group '{resource_group}'...")
    print_warning("This will delete ALL resources in the group!")
    
    returncode, stdout, stderr = run_az_command(
        [
            'group', 'delete',
            '--name', resource_group,
            '--yes',
            '--no-wait'
        ],
        check=False,
        dry_run=dry_run,
        logger=logger
    )
    
    if returncode == 0:
        print_success(f"Resource group deletion initiated")
        print_info("Deletion is running in the background. This may take several minutes.")
        print_info(f"Check status: az group show --name {resource_group}")
        return True
    else:
        print_error(f"Failed to delete resource group: {stderr}")
        return False


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(verbose=True, log_file='azure-cleanup.log')
    
    print_header("DraftGenie Azure Cleanup")
    
    # Determine resource group
    resource_group = None
    
    if args.resource_group:
        resource_group = args.resource_group
    elif args.config and os.path.exists(args.config):
        config = load_config(args.config)
        resource_group = config.get('azure', {}).get('resource_group')
    else:
        print_error("Please specify --resource-group or --config")
        sys.exit(1)
    
    if not resource_group:
        print_error("Resource group not specified")
        sys.exit(1)
    
    print_info(f"Resource Group: {resource_group}")
    
    # Check if resource group exists
    returncode, stdout, stderr = run_az_command(
        ['group', 'exists', '--name', resource_group],
        check=False,
        logger=logger
    )
    
    if returncode != 0 or stdout.strip().lower() != 'true':
        print_warning(f"Resource group '{resource_group}' does not exist")
        sys.exit(0)
    
    # List resources
    print_info("\nListing resources in the group...")
    resources = list_resources_in_group(resource_group, logger)
    
    if resources:
        print_info(f"Found {len(resources)} resources:")
        for resource in resources:
            print_info(f"  - {resource['type']}: {resource['name']}")
    else:
        print_info("No resources found in the group")
    
    # Confirm deletion
    if not args.dry_run:
        print_warning("\n⚠️  WARNING: This will DELETE ALL resources in the group!")
        print_warning("This action CANNOT be undone!")
        
        if not confirm_action(
            f"\nAre you sure you want to delete resource group '{resource_group}'?",
            args.force
        ):
            print_info("Cleanup cancelled")
            sys.exit(0)
    
    # Delete resource group
    success = delete_resource_group(resource_group, args.dry_run, logger)
    
    if success:
        if not args.dry_run:
            print_success("\n✓ Cleanup initiated successfully")
            print_info("\nThe resource group and all its resources are being deleted.")
            print_info("This process runs in the background and may take 10-15 minutes.")
            print_info("\nTo check deletion status:")
            print_info(f"  az group show --name {resource_group}")
            print_info("\nTo list all resource groups:")
            print_info("  az group list --output table")
        else:
            print_success("\n✓ Dry run completed")
    else:
        print_error("\n✗ Cleanup failed")
        sys.exit(1)


if __name__ == '__main__':
    main()

