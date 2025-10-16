#!/usr/bin/env python3
"""
DraftGenie Azure Deployment Script - Idempotent & Stateful Version (v1)

This script provides an idempotent, stateful deployment orchestration system for
deploying DraftGenie to Microsoft Azure. It tracks deployment state, detects changes
in dependencies, and intelligently skips or re-executes steps as needed.

KEY FEATURES:
- Idempotent: Safe to run multiple times - only executes what's needed
- Stateful: Tracks completion status, timestamps, and dependency hashes
- Change Detection: Re-executes steps only when dependencies change
- Error Recovery: Preserves state on failure for easy resume
- Flexible State Storage: Local file (default) or Azure Blob Storage (configurable)

STATE STORAGE APPROACHES:

1. LOCAL FILE STORAGE (Default)
   Pros:
   - Simple setup - no additional Azure resources required
   - Fast access - no network latency
   - Works offline during development
   - Easy to inspect and debug (human-readable JSON)
   - No additional costs
   
   Cons:
   - Not shared across machines/CI runners
   - Can be lost if local environment is destroyed
   - Not suitable for team collaboration without version control
   - Manual sync required for multi-environment deployments
   
   Recommended for:
   - Local development and testing
   - Single-user deployments
   - CI/CD with persistent runners
   - Quick iterations and debugging

2. AZURE BLOB STORAGE (Optional)
   Pros:
   - Centralized state accessible from anywhere
   - Shared across team members and CI/CD pipelines
   - Durable and highly available
   - Supports concurrent deployments with proper locking
   - Audit trail via blob versioning
   
   Cons:
   - Requires Azure Storage Account (additional resource)
   - Network dependency - slower than local file
   - Additional cost (minimal - typically <$1/month)
   - More complex setup and authentication
   - Requires internet connectivity
   
   Recommended for:
   - Team environments with multiple deployers
   - CI/CD pipelines with ephemeral runners
   - Production deployments requiring audit trails
   - Multi-region deployments

SWITCHING BETWEEN STORAGE APPROACHES:
To use Azure Blob Storage instead of local file:
1. Set environment variable: export AZURE_STATE_STORAGE=blob
2. Configure in config.yaml:
   advanced:
     state_storage: blob
     state_blob_account: <storage-account-name>
     state_blob_container: deployment-state
     state_blob_name: azure-deployment-state.json
3. Ensure Azure CLI is authenticated with access to the storage account

Usage:
    python scripts/deploy-azure_v1.py [options]

Options:
    --config PATH          Path to configuration file (default: scripts/azure/config.yaml)
    --dry-run             Preview deployment without creating resources
    --verbose             Enable verbose logging
    --resume              Resume from last checkpoint
    --auto-approve        Auto-approve all prompts
    --force-step STEP     Force re-execution of specific step (e.g., 'create_databases')
    --force-all           Force re-execution of all steps, ignoring state
    --reset-state         Clear state file and start fresh
    --help                Show this help message

Examples:
    # Normal deployment (idempotent - skips completed steps)
    python scripts/deploy-azure_v1.py

    # Force re-execution of a specific step
    python scripts/deploy-azure_v1.py --force-step create_databases

    # Force complete re-deployment
    python scripts/deploy-azure_v1.py --force-all

    # Reset state and start fresh
    python scripts/deploy-azure_v1.py --reset-state

    # Resume from last checkpoint after failure
    python scripts/deploy-azure_v1.py --resume
"""

import sys
import os
import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from functools import wraps

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


class StateManager:
    """
    Manages deployment state with support for local file or Azure Blob Storage.
    
    State Structure:
    {
        "version": "1.0",
        "last_updated": "2024-01-15T10:30:00",
        "steps": {
            "step_name": {
                "status": "completed|failed|skipped",
                "timestamp": "2024-01-15T10:30:00",
                "dependency_hash": "sha256_hash_of_dependencies",
                "error": "error message if failed",
                "metadata": {}
            }
        },
        "resources": {
            "resource_type": {
                "name": "resource-name",
                "id": "azure-resource-id",
                ...
            }
        }
    }
    """
    
    def __init__(self, config: Dict[str, Any], logger):
        """Initialize state manager."""
        self.config = config
        self.logger = logger
        self.storage_type = self._determine_storage_type()
        self.state_file = config.get('advanced', {}).get('state_file', '.azure-deployment-state-v1.json')
        
        # Initialize state structure
        self.state = self._load_state()
    
    def _determine_storage_type(self) -> str:
        """Determine which storage backend to use."""
        # Check environment variable first
        env_storage = os.environ.get('AZURE_STATE_STORAGE', '').lower()
        if env_storage in ['blob', 'azure']:
            return 'blob'
        
        # Check config
        config_storage = self.config.get('advanced', {}).get('state_storage', 'local').lower()
        if config_storage in ['blob', 'azure']:
            return 'blob'
        
        return 'local'
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from storage backend."""
        if self.storage_type == 'blob':
            return self._load_state_from_blob()
        else:
            return self._load_state_from_file()
    
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
    
    def _load_state_from_blob(self) -> Dict[str, Any]:
        """Load state from Azure Blob Storage."""
        # TODO: Implement Azure Blob Storage backend
        # This would use Azure SDK to download state from blob storage
        # For now, fall back to local file
        print_warning("Azure Blob Storage backend not yet implemented, falling back to local file")
        return self._load_state_from_file()
    
    def _create_empty_state(self) -> Dict[str, Any]:
        """Create empty state structure."""
        return {
            "version": "1.0",
            "last_updated": None,
            "steps": {},
            "resources": {},
            "completed_steps": [],  # Legacy compatibility
            "created_resources": {}  # Legacy compatibility
        }
    
    def save(self):
        """Save state to storage backend."""
        self.state['last_updated'] = datetime.now().isoformat()
        
        if self.storage_type == 'blob':
            self._save_state_to_blob()
        else:
            self._save_state_to_file()
    
    def _save_state_to_file(self):
        """Save state to local file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            self.logger.info(f"Saved state to {self.state_file}")
        except Exception as e:
            self.logger.error(f"Failed to save state file: {e}")
    
    def _save_state_to_blob(self):
        """Save state to Azure Blob Storage."""
        # TODO: Implement Azure Blob Storage backend
        print_warning("Azure Blob Storage backend not yet implemented, falling back to local file")
        self._save_state_to_file()
    
    def reset(self):
        """Reset state to empty."""
        self.state = self._create_empty_state()
        self.save()
        print_success("State has been reset")
    
    def is_step_completed(self, step_name: str) -> bool:
        """Check if a step has been completed successfully."""
        return self.state['steps'].get(step_name, {}).get('status') == 'completed'
    
    def mark_step_completed(self, step_name: str, dependency_hash: str, metadata: Dict[str, Any] = None):
        """Mark a step as completed."""
        self.state['steps'][step_name] = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'dependency_hash': dependency_hash,
            'metadata': metadata or {}
        }
        
        # Legacy compatibility
        if step_name not in self.state['completed_steps']:
            self.state['completed_steps'].append(step_name)
        
        self.save()
    
    def mark_step_failed(self, step_name: str, error: str):
        """Mark a step as failed."""
        self.state['steps'][step_name] = {
            'status': 'failed',
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
        self.save()
    
    def get_step_hash(self, step_name: str) -> Optional[str]:
        """Get the dependency hash for a completed step."""
        return self.state['steps'].get(step_name, {}).get('dependency_hash')
    
    def store_resource(self, resource_type: str, resource_data: Dict[str, Any]):
        """Store resource information."""
        self.state['resources'][resource_type] = resource_data
        
        # Legacy compatibility
        self.state['created_resources'][resource_type] = resource_data
        
        self.save()
    
    def get_resource(self, resource_type: str) -> Optional[Dict[str, Any]]:
        """Get stored resource information."""
        return self.state['resources'].get(resource_type)


def compute_hash(data: Any) -> str:
    """
    Compute SHA-256 hash of data.
    
    Args:
        data: Data to hash (will be JSON-serialized)
    
    Returns:
        Hex digest of SHA-256 hash
    """
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data, sort_keys=True)
    else:
        data_str = str(data)
    
    return hashlib.sha256(data_str.encode()).hexdigest()


def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of SHA-256 hash, or empty string if file doesn't exist
    """
    if not os.path.exists(file_path):
        return ""

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def idempotent_step(
    step_name: str,
    dependencies: Optional[List[str]] = None,
    config_keys: Optional[List[str]] = None
):
    """
    Decorator to make deployment steps idempotent with change detection.

    This decorator wraps deployment step methods to:
    1. Check if the step has been completed before
    2. Compute a hash of the step's dependencies (files, config values)
    3. Compare with the stored hash from the last successful run
    4. Skip execution if completed and dependencies unchanged
    5. Re-execute if never run, failed before, or dependencies changed
    6. Update state only on successful completion

    Args:
        step_name: Unique identifier for the step
        dependencies: List of file paths that this step depends on
        config_keys: List of config keys (dot-notation) that this step depends on

    Example:
        @idempotent_step(
            step_name='create_databases',
            dependencies=['scripts/azure/azure_resources.py'],
            config_keys=['postgresql.sku', 'redis.sku']
        )
        def _step_create_databases(self) -> bool:
            # Implementation here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> bool:
            state_manager: StateManager = self.state_manager
            force_step = self.force_steps.get(step_name, False)
            force_all = self.force_all

            # Compute dependency hash
            dependency_hash = compute_dependency_hash(
                self.config,
                dependencies or [],
                config_keys or []
            )

            # Check if step should be skipped
            if not force_step and not force_all:
                if state_manager.is_step_completed(step_name):
                    stored_hash = state_manager.get_step_hash(step_name)

                    if stored_hash == dependency_hash:
                        print_info(f"✓ Step '{step_name}' already completed and dependencies unchanged - skipping")
                        return True
                    else:
                        print_warning(f"⚠ Step '{step_name}' dependencies changed - re-executing")

            if force_step:
                print_info(f"🔄 Forcing re-execution of step '{step_name}'")
            elif force_all:
                print_info(f"🔄 Force-all mode: executing step '{step_name}'")

            # Execute the step
            try:
                result = func(self, *args, **kwargs)

                if result:
                    # Mark as completed with current dependency hash
                    state_manager.mark_step_completed(
                        step_name,
                        dependency_hash,
                        metadata={'function': func.__name__}
                    )
                    return True
                else:
                    # Mark as failed
                    state_manager.mark_step_failed(step_name, "Step returned False")
                    return False

            except Exception as e:
                error_msg = f"Exception in step: {str(e)}"
                self.logger.exception(error_msg)
                state_manager.mark_step_failed(step_name, error_msg)
                raise

        return wrapper
    return decorator


def compute_dependency_hash(
    config: Dict[str, Any],
    file_dependencies: List[str],
    config_keys: List[str]
) -> str:
    """
    Compute a combined hash of all dependencies for a step.

    Args:
        config: Configuration dictionary
        file_dependencies: List of file paths to hash
        config_keys: List of config keys (dot-notation) to hash

    Returns:
        Combined SHA-256 hash of all dependencies
    """
    hash_components = []

    # Hash file dependencies
    for file_path in file_dependencies:
        file_hash = compute_file_hash(file_path)
        hash_components.append(f"file:{file_path}:{file_hash}")

    # Hash config values
    for key in config_keys:
        value = get_nested_config_value(config, key)
        value_hash = compute_hash(value)
        hash_components.append(f"config:{key}:{value_hash}")

    # Combine all hashes
    combined = "|".join(sorted(hash_components))
    return hashlib.sha256(combined.encode()).hexdigest()


def get_nested_config_value(config: Dict[str, Any], key_path: str) -> Any:
    """
    Get a nested config value using dot notation.

    Args:
        config: Configuration dictionary
        key_path: Dot-separated key path (e.g., 'postgresql.sku')

    Returns:
        Config value or None if not found
    """
    keys = key_path.split('.')
    value = config

    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None

    return value


class IdempotentDraftGenieDeployer(DraftGenieDeployer):
    """
    Extended deployer with idempotent step execution and change detection.

    This class wraps the original DraftGenieDeployer and adds:
    - State management with dependency tracking
    - Idempotent step execution
    - Change detection via hashing
    - Force execution options
    - Enhanced error recovery
    """

    def __init__(
        self,
        config: Dict[str, Any],
        logger,
        dry_run: bool = False,
        state_manager: StateManager = None,
        force_steps: Dict[str, bool] = None,
        force_all: bool = False
    ):
        """Initialize idempotent deployer."""
        # Initialize state manager
        self.state_manager = state_manager or StateManager(config, logger)
        self.force_steps = force_steps or {}
        self.force_all = force_all

        # Initialize parent with state from state manager
        # Convert new state format to legacy format for compatibility
        legacy_state = {
            'completed_steps': self.state_manager.state.get('completed_steps', []),
            'created_resources': self.state_manager.state.get('created_resources', {})
        }

        super().__init__(config, logger, dry_run, legacy_state)

        # Override parent's state with our state manager's state
        self.state = self.state_manager.state

    def _save_deployment_state(self):
        """Override parent's state saving to use our state manager."""
        self.state_manager.save()

    # Wrap all deployment steps with idempotent decorator

    @idempotent_step(
        step_name='check_prerequisites',
        dependencies=['scripts/azure/prerequisites.py']
    )
    def _step_check_prerequisites(self) -> bool:
        """Check all prerequisites (idempotent)."""
        return super()._step_check_prerequisites()

    @idempotent_step(
        step_name='create_resource_group',
        dependencies=['scripts/azure/azure_resources.py'],
        config_keys=['azure.resource_group', 'azure.location']
    )
    def _step_create_resource_group(self) -> bool:
        """Create Azure resource group (idempotent)."""
        return super()._step_create_resource_group()

    @idempotent_step(
        step_name='create_monitoring',
        dependencies=['scripts/azure/azure_resources.py'],
        config_keys=['monitoring.log_workspace', 'monitoring.app_insights']
    )
    def _step_create_monitoring(self) -> bool:
        """Create monitoring infrastructure (idempotent)."""
        return super()._step_create_monitoring()

    @idempotent_step(
        step_name='create_container_registry',
        dependencies=['scripts/azure/azure_resources.py'],
        config_keys=['container_registry.name', 'container_registry.sku']
    )
    def _step_create_container_registry(self) -> bool:
        """Create Azure Container Registry (idempotent)."""
        return super()._step_create_container_registry()

    @idempotent_step(
        step_name='create_key_vault',
        dependencies=['scripts/azure/azure_resources.py'],
        config_keys=['key_vault.name']
    )
    def _step_create_key_vault(self) -> bool:
        """Create Azure Key Vault (idempotent)."""
        return super()._step_create_key_vault()

    @idempotent_step(
        step_name='create_databases',
        dependencies=['scripts/azure/azure_resources.py'],
        config_keys=[
            'postgresql.server_name', 'postgresql.sku', 'postgresql.tier',
            'postgresql.version', 'postgresql.storage_size',
            'redis.name', 'redis.sku', 'redis.vm_size'
        ]
    )
    def _step_create_databases(self) -> bool:
        """Create database services (idempotent)."""
        return super()._step_create_databases()

    @idempotent_step(
        step_name='store_secrets',
        dependencies=['scripts/azure/azure_resources.py'],
        config_keys=['secrets.gemini_api_key']
    )
    def _step_store_secrets(self) -> bool:
        """Store secrets in Key Vault (idempotent)."""
        return super()._step_store_secrets()

    @idempotent_step(
        step_name='create_container_apps_env',
        dependencies=['scripts/azure/azure_resources.py'],
        config_keys=['container_apps.environment_name']
    )
    def _step_create_container_apps_env(self) -> bool:
        """Create Container Apps environment (idempotent)."""
        return super()._step_create_container_apps_env()

    @idempotent_step(
        step_name='build_and_push_images',
        dependencies=[
            'scripts/azure/docker_builder.py',
            'docker/Dockerfile.api-gateway',
            'docker/Dockerfile.speaker-service',
            'docker/Dockerfile.draft-service',
            'docker/Dockerfile.rag-service',
            'docker/Dockerfile.evaluation-service'
        ],
        config_keys=['docker.dockerfiles']
    )
    def _step_build_and_push_images(self) -> bool:
        """Build and push Docker images (idempotent)."""
        return super()._step_build_and_push_images()

    @idempotent_step(
        step_name='deploy_infrastructure_services',
        dependencies=['scripts/azure/container_apps.py'],
        config_keys=['services.rabbitmq', 'services.qdrant']
    )
    def _step_deploy_infrastructure_services(self) -> bool:
        """Deploy infrastructure services (idempotent)."""
        return super()._step_deploy_infrastructure_services()

    @idempotent_step(
        step_name='deploy_application_services',
        dependencies=['scripts/azure/container_apps.py'],
        config_keys=[
            'services.api_gateway', 'services.speaker_service',
            'services.draft_service', 'services.rag_service',
            'services.evaluation_service'
        ]
    )
    def _step_deploy_application_services(self) -> bool:
        """Deploy application services (idempotent)."""
        return super()._step_deploy_application_services()

    @idempotent_step(
        step_name='configure_environment_variables',
        dependencies=['scripts/azure/env_configurator.py']
    )
    def _step_configure_environment_variables(self) -> bool:
        """Configure environment variables (idempotent)."""
        return super()._step_configure_environment_variables()

    @idempotent_step(
        step_name='run_migrations',
        config_keys=['deployment.skip_migrations']
    )
    def _step_run_migrations(self) -> bool:
        """Run database migrations (idempotent)."""
        return super()._step_run_migrations()

    @idempotent_step(
        step_name='verify_deployment'
    )
    def _step_verify_deployment(self) -> bool:
        """Verify deployment (idempotent)."""
        return super()._step_verify_deployment()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Deploy DraftGenie to Microsoft Azure (Idempotent & Stateful)',
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

    parser.add_argument(
        '--force-step',
        type=str,
        action='append',
        dest='force_steps',
        help='Force re-execution of specific step (can be used multiple times)'
    )

    parser.add_argument(
        '--force-all',
        action='store_true',
        help='Force re-execution of all steps, ignoring state'
    )

    parser.add_argument(
        '--reset-state',
        action='store_true',
        help='Clear state file and start fresh'
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


def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(
        verbose=args.verbose,
        log_file='azure-deployment-v1.log'
    )

    print_header("DraftGenie Azure Deployment (Idempotent & Stateful v1)")

    # Load configuration
    config_path = args.config

    if not os.path.exists(config_path):
        print_error(f"Configuration file not found: {config_path}")
        print_info("Please create a configuration file. See scripts/azure/config.template.yaml")
        sys.exit(1)

    print_info(f"Loading configuration from {config_path}")
    config = load_config(config_path)

    # Override config with command line arguments
    if args.dry_run:
        config.setdefault('deployment', {})['dry_run'] = True
    if args.verbose:
        config.setdefault('deployment', {})['verbose'] = True
    if args.auto_approve:
        config.setdefault('deployment', {})['auto_approve'] = True
    if args.resume:
        config.setdefault('deployment', {})['resume'] = True

    # Validate configuration
    if not validate_config(config):
        sys.exit(1)

    # Initialize state manager
    state_manager = StateManager(config, logger)

    # Handle reset-state
    if args.reset_state:
        print_warning("⚠️  Resetting deployment state...")
        if confirm_action("Are you sure you want to reset the state?", args.auto_approve):
            state_manager.reset()
            print_success("State has been reset. You can now run a fresh deployment.")
        else:
            print_info("State reset cancelled")
        sys.exit(0)

    # Parse force-step arguments
    force_steps = {}
    if args.force_steps:
        for step in args.force_steps:
            force_steps[step] = True
        print_info(f"Force re-execution enabled for steps: {', '.join(args.force_steps)}")

    if args.force_all:
        print_warning("⚠️  Force-all mode enabled - all steps will be re-executed")

    # Show deployment summary
    print_info("\n=== Deployment Configuration ===")
    print_info(f"Resource Group: {config['azure']['resource_group']}")
    location = config.get('locations', {}).get('default', config.get('azure', {}).get('location'))
    print_info(f"Default Location: {location}")
    print_info(f"Container Registry: {config['container_registry']['name']}")
    print_info(f"Key Vault: {config['key_vault']['name']}")
    print_info(f"Dry Run: {config.get('deployment', {}).get('dry_run', False)}")
    print_info(f"State Storage: {state_manager.storage_type}")
    print_info(f"State File: {state_manager.state_file}")

    # Show state summary
    if state_manager.state.get('steps'):
        completed_count = sum(
            1 for step in state_manager.state['steps'].values()
            if step.get('status') == 'completed'
        )
        total_steps = len(state_manager.state['steps'])
        print_info(f"Previous State: {completed_count}/{total_steps} steps completed")

        if state_manager.state.get('last_updated'):
            print_info(f"Last Updated: {state_manager.state['last_updated']}")

    # Confirm deployment
    if not config.get('deployment', {}).get('dry_run', False):
        if not confirm_action("\nProceed with deployment?", config.get('deployment', {}).get('auto_approve', False)):
            print_info("Deployment cancelled")
            sys.exit(0)

    # Create deployer and execute
    deployer = IdempotentDraftGenieDeployer(
        config=config,
        logger=logger,
        dry_run=config.get('deployment', {}).get('dry_run', False),
        state_manager=state_manager,
        force_steps=force_steps,
        force_all=args.force_all
    )

    try:
        success = deployer.deploy()

        if success:
            print_success("\n🎉 Deployment completed successfully!")
            print_info(f"\nState saved to: {state_manager.state_file}")
            print_info("You can safely re-run this script - it will skip completed steps.")
            sys.exit(0)
        else:
            print_error("\n❌ Deployment failed")
            print_info(f"\nState saved to: {state_manager.state_file}")
            print_info("Fix the errors and re-run the script to resume from where it failed.")
            sys.exit(1)

    except KeyboardInterrupt:
        print_warning("\n\n⚠️  Deployment interrupted by user")
        print_info(f"State saved to: {state_manager.state_file}")
        print_info("Re-run the script with --resume to continue from where you left off.")
        sys.exit(130)

    except Exception as e:
        print_error(f"\n❌ Deployment failed with exception: {str(e)}")
        logger.exception("Deployment error")
        print_info(f"\nState saved to: {state_manager.state_file}")
        print_info("Fix the errors and re-run the script to resume.")
        sys.exit(1)


if __name__ == '__main__':
    main()


