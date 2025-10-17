#!/usr/bin/env python3
"""
Build and Push Individual Service to Azure Container Registry

This script allows you to build and push a single service's Docker image
to Azure Container Registry using the existing docker_builder module.

Usage:
    python scripts/build-push-service.py api-gateway
    python scripts/build-push-service.py speaker-service
    python scripts/build-push-service.py draft-service
    python scripts/build-push-service.py rag-service
    python scripts/build-push-service.py evaluation-service

Options:
    --tag TAG           Image tag (default: latest)
    --dry-run           Dry run mode, don't execute commands
    --skip-login        Skip registry login
    --skip-build        Skip build, only push
    --skip-push         Build only, skip push
    --config PATH       Path to config file (default: scripts/azure/config.yaml)

Examples:
    # Build and push API Gateway with custom tag
    python scripts/build-push-service.py api-gateway --tag v1.0.1
    
    # Build only (don't push)
    python scripts/build-push-service.py api-gateway --skip-push
    
    # Dry run to see what would happen
    python scripts/build-push-service.py api-gateway --dry-run
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add scripts/azure to Python path
script_dir = Path(__file__).parent
azure_dir = script_dir / 'azure'
sys.path.insert(0, str(azure_dir))

from docker_builder import DockerBuilder
from utils import (
    print_header, print_success, print_error, print_warning, print_info,
    load_config, setup_logging
)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Build and push individual service to Azure Container Registry',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'service',
        choices=['api-gateway', 'speaker-service', 'draft-service', 'rag-service', 'evaluation-service'],
        help='Service to build and push'
    )
    
    parser.add_argument(
        '--tag',
        default='latest',
        help='Image tag (default: latest)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode, don\'t execute commands'
    )
    
    parser.add_argument(
        '--skip-login',
        action='store_true',
        help='Skip registry login'
    )
    
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip build, only push'
    )
    
    parser.add_argument(
        '--skip-push',
        action='store_true',
        help='Build only, skip push'
    )
    
    parser.add_argument(
        '--config',
        default='scripts/azure/config.yaml',
        help='Path to config file (default: scripts/azure/config.yaml)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def get_registry_info(config):
    """Get registry information from config."""
    registry_name = config['container_registry']['name']
    
    return {
        'name': registry_name,
        'login_server': f"{registry_name}.azurecr.io"
    }


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(
        verbose=args.verbose,
        log_file=f'build-push-{args.service}.log'
    )
    
    print_header(f"Building and Pushing: {args.service}")
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print_error(f"Configuration file not found: {config_path}")
        print_info("Please create a configuration file. See scripts/azure/config.template.yaml")
        sys.exit(1)
    
    try:
        config = load_config(str(config_path))
        print_success(f"Loaded configuration from {config_path}")
    except Exception as e:
        print_error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)
    
    # Get registry info
    registry_info = get_registry_info(config)
    print_info(f"Registry: {registry_info['login_server']}")
    print_info(f"Service: {args.service}")
    print_info(f"Tag: {args.tag}")
    
    if args.dry_run:
        print_warning("DRY RUN MODE - No actual changes will be made")
    
    # Create Docker builder
    builder = DockerBuilder(config, registry_info, logger, args.dry_run)
    
    try:
        # Login to registry
        if not args.skip_login:
            print_header("Logging in to Container Registry")
            success, message = builder.login_to_registry()
            if not success:
                print_error(f"Failed to login to registry: {message}")
                sys.exit(1)
            print_success("Successfully logged in to registry")
        else:
            print_warning("Skipping registry login (--skip-login)")
        
        # Build image
        if not args.skip_build:
            print_header("Building Docker Image")
            success, image_name = builder.build_image(args.service, args.tag)
            if not success:
                print_error(f"Failed to build image: {image_name}")
                sys.exit(1)
            print_success(f"Successfully built image: {image_name}")
        else:
            print_warning("Skipping build (--skip-build)")
            image_name = builder.get_image_name(args.service, args.tag)
        
        # Push image
        if not args.skip_push:
            print_header("Pushing Docker Image")
            # Get the full image name if we skipped the build
            if args.skip_build:
                image_name = builder.get_image_name(args.service, args.tag)
            success, message = builder.push_image(image_name)
            if not success:
                print_error(f"Failed to push image: {message}")
                sys.exit(1)
            print_success(f"Successfully pushed image: {image_name}")
        else:
            print_warning("Skipping push (--skip-push)")
        
        # Summary
        print_header("Summary")
        print_success(f"Service: {args.service}")
        print_success(f"Image: {image_name}")
        print_success(f"Registry: {registry_info['login_server']}")
        
        if args.dry_run:
            print_warning("DRY RUN MODE - No actual changes were made")
        
        print_success("\n🎉 Done!")
        
        # Print next steps
        print_header("Next Steps")
        print_info("To update the running container app with the new image:")
        print_info(f"  az containerapp update \\")
        print_info(f"    --name {args.service} \\")
        print_info(f"    --resource-group draftgenie-rg \\")
        print_info(f"    --image {image_name}")
        print_info("")
        print_info("Or restart the container app to pull the latest image:")
        print_info(f"  az containerapp revision restart \\")
        print_info(f"    --name {args.service} \\")
        print_info(f"    --resource-group draftgenie-rg")
        
    except KeyboardInterrupt:
        print_warning("\n\nInterrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print_error(f"\nFailed with exception: {str(e)}")
        logger.exception("Build and push error")
        sys.exit(1)


if __name__ == '__main__':
    main()

