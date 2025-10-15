#!/usr/bin/env python3
"""
DraftGenie Azure Deployment Script

This script automates the deployment of DraftGenie to Microsoft Azure,
following the steps outlined in docs/deployment/azure-deployment-guide.md.

Usage:
    python scripts/deploy-azure.py [options]

Options:
    --config PATH       Path to configuration file (default: scripts/azure/config.yaml)
    --dry-run          Preview deployment without creating resources
    --verbose          Enable verbose logging
    --resume           Resume from last checkpoint
    --auto-approve     Auto-approve all prompts
    --help             Show this help message

Examples:
    # Interactive deployment with default config
    python scripts/deploy-azure.py

    # Dry run to preview deployment
    python scripts/deploy-azure.py --dry-run

    # Resume from last checkpoint
    python scripts/deploy-azure.py --resume

    # Non-interactive deployment
    python scripts/deploy-azure.py --auto-approve
"""

import sys
import os
import argparse
from pathlib import Path

# Add azure module to path
script_dir = Path(__file__).parent
azure_dir = script_dir / 'azure'
sys.path.insert(0, str(azure_dir))

from utils import (
    setup_logging, load_config, save_config, load_state, save_state,
    print_header, print_success, print_error, print_warning, print_info,
    confirm_action, validate_resource_name, generate_password, generate_secret
)
from deployer import DraftGenieDeployer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Deploy DraftGenie to Microsoft Azure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='scripts/azure/config.yaml',
        help='Path to configuration file (default: scripts/azure/config.yaml)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview deployment without creating resources'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )
    
    parser.add_argument(
        '--auto-approve',
        action='store_true',
        help='Auto-approve all prompts'
    )
    
    return parser.parse_args()


def validate_config(config: dict) -> bool:
    """
    Validate configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, False otherwise
    """
    errors = []
    
    # Check required fields
    if not config.get('azure', {}).get('resource_group'):
        errors.append("Azure resource group name is required")
    
    if 'locations' not in config and not config.get('azure', {}).get('location'):
        errors.append("Either 'azure.location' or 'locations.default' is required")
    
    if 'locations' in config and 'default' not in config['locations']:
        errors.append("'locations.default' is required when 'locations' is defined")
    
    if not config.get('container_registry', {}).get('name'):
        errors.append("Container registry name is required")
    
    if not config.get('key_vault', {}).get('name'):
        errors.append("Key Vault name is required")
    
    if not config.get('secrets', {}).get('gemini_api_key'):
        errors.append("Gemini API key is required")
    
    # Validate resource names
    acr_name = config.get('container_registry', {}).get('name', '')
    if acr_name and not validate_resource_name(acr_name, 'container_registry'):
        errors.append(f"Invalid container registry name: {acr_name} (must be alphanumeric only)")
    
    kv_name = config.get('key_vault', {}).get('name', '')
    if kv_name and not validate_resource_name(kv_name, 'key_vault'):
        errors.append(f"Invalid Key Vault name: {kv_name} (must be alphanumeric and hyphens)")
    
    # Print errors
    if errors:
        print_error("Configuration validation failed:")
        for error in errors:
            print_error(f"  - {error}")
        return False
    
    return True


def interactive_config_setup(config_path: str) -> dict:
    """
    Interactive configuration setup.
    
    Args:
        config_path: Path to save configuration
        
    Returns:
        Configuration dictionary
    """
    print_header("DraftGenie Azure Deployment - Configuration Setup")
    
    print_info("This wizard will help you configure your Azure deployment.")
    print_info("Press Enter to use default values shown in [brackets].\n")
    
    config = {
        'azure': {},
        'container_registry': {},
        'key_vault': {},
        'monitoring': {},
        'postgresql': {},
        'redis': {},
        'mongodb': {},
        'container_apps': {},
        'services': {},
        'secrets': {},
        'deployment': {},
        'docker': {},
        'networking': {},
        'tags': {},
        'advanced': {}
    }
    
    # Azure configuration
    print_info("=== Azure Configuration ===")
    
    config['azure']['subscription_id'] = input("Azure Subscription ID (leave empty for default): ").strip()
    
    default_rg = "draftgenie-rg"
    rg = input(f"Resource Group Name [{default_rg}]: ").strip() or default_rg
    config['azure']['resource_group'] = rg
    
    default_location = "eastus"
    location = input(f"Azure Region [{default_location}]: ").strip() or default_location
    config['azure']['location'] = location
    
    default_project = "draftgenie"
    project = input(f"Project Name [{default_project}]: ").strip() or default_project
    config['azure']['project_name'] = project
    
    # Container Registry
    print_info("\n=== Container Registry ===")
    
    default_acr = f"{project}acr{os.urandom(4).hex()}"
    acr = input(f"Registry Name [{default_acr}]: ").strip() or default_acr
    config['container_registry']['name'] = acr
    config['container_registry']['sku'] = 'Basic'
    
    # Key Vault
    print_info("\n=== Key Vault ===")
    
    default_kv = f"{project}-kv-{os.urandom(4).hex()}"
    kv = input(f"Key Vault Name [{default_kv}]: ").strip() or default_kv
    config['key_vault']['name'] = kv
    
    # Monitoring
    config['monitoring']['log_workspace'] = f"{project}-logs"
    config['monitoring']['app_insights'] = f"{project}-insights"
    
    # PostgreSQL
    print_info("\n=== PostgreSQL Database ===")
    
    default_pg = f"{project}-postgres"
    pg = input(f"PostgreSQL Server Name [{default_pg}]: ").strip() or default_pg
    config['postgresql']['server_name'] = pg
    config['postgresql']['database_name'] = project
    config['postgresql']['admin_user'] = project
    config['postgresql']['admin_password'] = ""  # Will be auto-generated
    config['postgresql']['sku'] = 'Standard_B1ms'
    config['postgresql']['tier'] = 'Burstable'
    config['postgresql']['version'] = '16'
    config['postgresql']['storage_size'] = 32
    
    # Redis
    print_info("\n=== Redis Cache ===")
    
    default_redis = f"{project}-redis"
    redis = input(f"Redis Cache Name [{default_redis}]: ").strip() or default_redis
    config['redis']['name'] = redis
    config['redis']['sku'] = 'Basic'
    config['redis']['vm_size'] = 'c0'
    
    # MongoDB
    print_info("\n=== MongoDB Atlas ===")
    print_info("You'll need to set up MongoDB Atlas separately.")
    
    mongodb_url = input("MongoDB Connection URL (leave empty to set up later): ").strip()
    config['mongodb']['connection_url'] = mongodb_url
    
    # Container Apps
    config['container_apps']['environment_name'] = f"{project}-env"
    
    # Secrets
    print_info("\n=== API Keys and Secrets ===")
    
    gemini_key = input("Google Gemini API Key (required): ").strip()
    if not gemini_key:
        print_error("Gemini API key is required!")
        sys.exit(1)
    
    config['secrets']['gemini_api_key'] = gemini_key
    config['secrets']['jwt_secret'] = ""  # Will be auto-generated
    config['secrets']['rabbitmq_password'] = ""  # Will be auto-generated
    
    # Load default service configurations
    config['services'] = load_default_service_config(project)
    
    # Deployment options
    config['deployment']['skip_build'] = False
    config['deployment']['skip_migrations'] = False
    config['deployment']['dry_run'] = False
    config['deployment']['auto_approve'] = False
    config['deployment']['verbose'] = False
    config['deployment']['resume'] = False
    
    # Docker
    config['docker'] = load_default_docker_config()
    
    # Networking
    config['networking']['cors_origin'] = '*'
    config['networking']['swagger_enabled'] = True
    config['networking']['swagger_path'] = 'api/docs'
    
    # Tags
    config['tags'] = {
        'Environment': 'production',
        'Project': 'DraftGenie',
        'ManagedBy': 'deployment-script',
        'Owner': ''
    }
    
    # Advanced
    config['advanced'] = {
        'retry_attempts': 3,
        'retry_delay': 5,
        'operation_timeout': 600,
        'cleanup_on_failure': False,
        'save_state': True,
        'state_file': '.azure-deployment-state.json'
    }
    
    # Save configuration
    print_info(f"\nSaving configuration to {config_path}...")
    save_config(config, config_path)
    print_success("Configuration saved!")
    
    return config


def load_default_service_config(project_name: str) -> dict:
    """Load default service configuration."""
    return {
        'api_gateway': {
            'name': 'api-gateway',
            'port': 3000,
            'cpu': 0.5,
            'memory': '1Gi',
            'min_replicas': 1,
            'max_replicas': 5,
            'ingress': 'external'
        },
        'speaker_service': {
            'name': 'speaker-service',
            'port': 3001,
            'cpu': 0.5,
            'memory': '1Gi',
            'min_replicas': 1,
            'max_replicas': 3,
            'ingress': 'internal'
        },
        'draft_service': {
            'name': 'draft-service',
            'port': 3002,
            'cpu': 0.5,
            'memory': '1Gi',
            'min_replicas': 1,
            'max_replicas': 3,
            'ingress': 'internal'
        },
        'rag_service': {
            'name': 'rag-service',
            'port': 3003,
            'cpu': 1.0,
            'memory': '2Gi',
            'min_replicas': 1,
            'max_replicas': 3,
            'ingress': 'internal'
        },
        'evaluation_service': {
            'name': 'evaluation-service',
            'port': 3004,
            'cpu': 0.5,
            'memory': '1Gi',
            'min_replicas': 1,
            'max_replicas': 3,
            'ingress': 'internal'
        },
        'rabbitmq': {
            'name': 'rabbitmq',
            'port': 5672,
            'cpu': 0.5,
            'memory': '1Gi',
            'min_replicas': 1,
            'max_replicas': 1,
            'ingress': 'internal',
            'image': 'rabbitmq:3.13-management-alpine'
        },
        'qdrant': {
            'name': 'qdrant',
            'port': 6333,
            'cpu': 0.5,
            'memory': '1Gi',
            'min_replicas': 1,
            'max_replicas': 1,
            'ingress': 'internal',
            'image': 'qdrant/qdrant:v1.7.4'
        }
    }


def load_default_docker_config() -> dict:
    """Load default Docker configuration."""
    return {
        'registry': '',
        'build_context': '.',
        'dockerfiles': {
            'api_gateway': 'docker/Dockerfile.api-gateway',
            'speaker_service': 'docker/Dockerfile.speaker-service',
            'draft_service': 'docker/Dockerfile.draft-service',
            'rag_service': 'docker/Dockerfile.rag-service',
            'evaluation_service': 'docker/Dockerfile.evaluation-service'
        }
    }


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(
        verbose=args.verbose,
        log_file='azure-deployment.log'
    )
    
    print_header("DraftGenie Azure Deployment")
    
    # Load or create configuration
    config_path = args.config
    
    if not os.path.exists(config_path):
        print_warning(f"Configuration file not found: {config_path}")
        
        if confirm_action("Would you like to create a new configuration?", args.auto_approve):
            config = interactive_config_setup(config_path)
        else:
            print_error("Configuration required. Exiting.")
            sys.exit(1)
    else:
        print_info(f"Loading configuration from {config_path}")
        config = load_config(config_path)
    
    # Override config with command line arguments
    if args.dry_run:
        config['deployment']['dry_run'] = True
    if args.verbose:
        config['deployment']['verbose'] = True
    if args.auto_approve:
        config['deployment']['auto_approve'] = True
    if args.resume:
        config['deployment']['resume'] = True
    
    # Validate configuration
    if not validate_config(config):
        sys.exit(1)
    
    # Load state if resuming
    state = None
    if args.resume:
        state_file = config['advanced'].get('state_file', '.azure-deployment-state.json')
        if os.path.exists(state_file):
            print_info(f"Resuming from {state_file}")
            state = load_state(state_file)
        else:
            print_warning(f"State file not found: {state_file}")
            print_info("Starting fresh deployment")
    
    # Show deployment summary
    print_info("\n=== Deployment Summary ===")
    print_info(f"Resource Group: {config['azure']['resource_group']}")
    location = config.get('locations', {}).get('default', config.get('azure', {}).get('location'))
    print_info(f"Default Location: {location}")
    print_info(f"Container Registry: {config['container_registry']['name']}")
    print_info(f"Key Vault: {config['key_vault']['name']}")
    print_info(f"Dry Run: {config['deployment']['dry_run']}")
    
    # Confirm deployment
    if not config['deployment']['dry_run']:
        if not confirm_action("\nProceed with deployment?", config['deployment']['auto_approve']):
            print_info("Deployment cancelled")
            sys.exit(0)
    
    # Create deployer and execute
    deployer = DraftGenieDeployer(
        config=config,
        logger=logger,
        dry_run=config['deployment']['dry_run'],
        state=state
    )
    
    success = deployer.deploy()
    
    if success:
        print_success("\n🎉 Deployment completed successfully!")
        sys.exit(0)
    else:
        print_error("\n❌ Deployment failed")
        sys.exit(1)


if __name__ == '__main__':
    main()

