"""
Azure resource creation and management.
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, Tuple
import logging

from utils import (
    print_header, print_success, print_error, print_warning, print_info,
    print_step, run_az_command, generate_password
)


class AzureResourceManager:
    """Manage Azure resources for DraftGenie deployment."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        logger: logging.Logger,
        dry_run: bool = False,
        state: Dict[str, Any] = None
    ):
        """
        Initialize Azure resource manager.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
            dry_run: Dry run mode
            state: Deployment state dictionary
        """
        self.config = config
        self.logger = logger
        self.dry_run = dry_run
        self.state = state or {'completed_steps': [], 'created_resources': {}}
        
        # Extract common config values
        self.resource_group = config['azure']['resource_group']
        self.project_name = config['azure']['project_name']
        self.tags = self._format_tags(config.get('tags', {}))

        if 'locations' in config and 'default' in config['locations']:
            if 'location' in config['azure']:
                self.logger.warning("Both 'azure.location' and 'locations' are defined. Using 'locations'.")
        elif 'location' not in config['azure']:
            raise ValueError("Either 'azure.location' or 'locations.default' must be defined in the config.")
    
    def _format_tags(self, tags: Dict[str, str]) -> str:
        """
        Format tags for Azure CLI.
        
        Args:
            tags: Tags dictionary
            
        Returns:
            Formatted tags string
        """
        if not tags:
            return ""
        
        tag_pairs = [f"{k}={v}" for k, v in tags.items() if v]
        return " ".join(tag_pairs)
    
    def _is_step_completed(self, step_name: str) -> bool:
        """Check if a step has been completed."""
        return step_name in self.state.get('completed_steps', [])
    
    def _mark_step_completed(self, step_name: str):
        """Mark a step as completed."""
        if step_name not in self.state.get('completed_steps', []):
            self.state['completed_steps'].append(step_name)
    
    def _save_resource(self, resource_type: str, resource_data: Dict[str, Any]):
        """Save resource information to state."""
        if 'created_resources' not in self.state:
            self.state['created_resources'] = {}
        self.state['created_resources'][resource_type] = resource_data

    def _get_location_for_resource(self, resource_type: str) -> str:
        """
        Get the location for a specific resource type.
        Falls back to the default location if no specific location is defined.
        """
        if 'locations' in self.config and 'default' in self.config['locations']:
            return self.config.get('locations', {}).get(resource_type, self.config['locations']['default'])
        return self.config['azure']['location']

    def create_resource_group(self) -> Tuple[bool, str]:
        """
        Create Azure resource group.
        
        Returns:
            Tuple of (success, message)
        """
        step_name = "create_resource_group"
        
        # Idempotency check
        exists_returncode, _, _ = run_az_command(
            ['group', 'exists', '--name', self.resource_group],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        if exists_returncode == 0:
            print_info(f"Resource group '{self.resource_group}' already exists, skipping creation.")
            self._mark_step_completed(step_name)
            return True, f"Resource group '{self.resource_group}' already exists"

        location = self._get_location_for_resource('resource_group')
        print_info(f"Creating resource group '{self.resource_group}' in {location}...")
        
        cmd = [
            'group', 'create',
            '--name', self.resource_group,
            '--location', location
        ]
        
        if self.tags:
            cmd.extend(['--tags', self.tags])
        
        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode == 0:
            self._mark_step_completed(step_name)
            self._save_resource('resource_group', {
                'name': self.resource_group,
                'location': location
            })
            return True, f"Resource group '{self.resource_group}' created"
        else:
            return False, f"Failed to create resource group: {stderr}"
    
    def create_container_registry(self) -> Tuple[bool, Dict[str, str]]:
        """
        Create Azure Container Registry.
        
        Returns:
            Tuple of (success, registry_info)
        """
        step_name = "create_container_registry"
        registry_name = self.config['container_registry']['name']

        # Idempotency check
        returncode, _, stderr = run_az_command(
            ['acr', 'show', '--name', registry_name, '--resource-group', self.resource_group],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        if returncode == 0:
            print_info(f"Container registry '{registry_name}' already exists, skipping creation.")
            self._mark_step_completed(step_name)
            # Still need to fetch credentials if not in state
            if 'container_registry' not in self.state['created_resources']:
                 return self._get_container_registry_credentials(registry_name)
            return True, self.state['created_resources']['container_registry']

        sku = self.config['container_registry']['sku']
        
        print_info(f"Creating container registry '{registry_name}'...")
        
        cmd = [
            'acr', 'create',
            '--resource-group', self.resource_group,
            '--name', registry_name,
            '--sku', sku,
            '--admin-enabled', 'true'
        ]
        
        if self.tags:
            cmd.extend(['--tags', self.tags])
        
        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode != 0:
            return False, {'error': f"Failed to create container registry: {stderr}"}
        
        # Get registry credentials
        returncode, stdout, stderr = run_az_command(
            ['acr', 'credential', 'show', '--name', registry_name],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode == 0 and not self.dry_run:
            creds = json.loads(stdout)
            registry_info = {
                'name': registry_name,
                'login_server': f"{registry_name}.azurecr.io",
                'username': creds.get('username'),
                'password': creds['passwords'][0]['value'] if creds.get('passwords') else None
            }
        else:
            registry_info = {
                'name': registry_name,
                'login_server': f"{registry_name}.azurecr.io"
            }
        
        self._mark_step_completed(step_name)
        self._save_resource('container_registry', registry_info)
        
        return True, registry_info
    
    def _get_container_registry_credentials(self, registry_name: str) -> Tuple[bool, Dict[str, str]]:
        """Get credentials for an existing container registry."""
        returncode, stdout, stderr = run_az_command(
            ['acr', 'credential', 'show', '--name', registry_name],
            check=False, dry_run=self.dry_run, logger=self.logger
        )

        if returncode == 0 and not self.dry_run:
            creds = json.loads(stdout)
            registry_info = {
                'name': registry_name,
                'login_server': f"{registry_name}.azurecr.io",
                'username': creds.get('username'),
                'password': creds['passwords'][0]['value'] if creds.get('passwords') else None
            }
        else:
            registry_info = {
                'name': registry_name,
                'login_server': f"{registry_name}.azurecr.io"
            }
        
        self._save_resource('container_registry', registry_info)
        return True, registry_info

    def create_key_vault(self) -> Tuple[bool, str]:
        """
        Create Azure Key Vault.
        
        Returns:
            Tuple of (success, key_vault_name)
        """
        step_name = "create_key_vault"
        kv_name = self.config['key_vault']['name']

        # Idempotency check
        returncode, _, stderr = run_az_command(
            ['keyvault', 'show', '--name', kv_name, '--resource-group', self.resource_group],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        if returncode == 0:
            print_info(f"Key Vault '{kv_name}' already exists, skipping creation.")
            self._mark_step_completed(step_name)
            self._save_resource('key_vault', {'name': kv_name})
            return True, kv_name
        
        print_info(f"Creating Key Vault '{kv_name}'...")
        
        cmd = [
            'keyvault', 'create',
            '--resource-group', self.resource_group,
            '--name', kv_name,
            '--location', self._get_location_for_resource('key_vault'),
            '--enable-rbac-authorization', 'false'
        ]
        
        if self.tags:
            cmd.extend(['--tags', self.tags])
        
        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode == 0:
            self._mark_step_completed(step_name)
            self._save_resource('key_vault', {'name': kv_name})
            return True, kv_name
        else:
            return False, f"Failed to create Key Vault: {stderr}"
    
    def create_log_analytics_workspace(self) -> Tuple[bool, str]:
        """
        Create Log Analytics Workspace.
        
        Returns:
            Tuple of (success, workspace_id)
        """
        step_name = "create_log_analytics"
        workspace_name = self.config['monitoring']['log_workspace']

        # Idempotency check
        returncode, _, stderr = run_az_command(
            ['monitor', 'log-analytics', 'workspace', 'show', '--workspace-name', workspace_name, '--resource-group', self.resource_group],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        if returncode == 0:
            print_info(f"Log Analytics workspace '{workspace_name}' already exists, skipping creation.")
            self._mark_step_completed(step_name)
            if 'log_analytics' not in self.state['created_resources']:
                return self._get_log_analytics_workspace_id(workspace_name)
            return True, self.state['created_resources']['log_analytics']['id']
        
        print_info(f"Creating Log Analytics workspace '{workspace_name}'...")
        
        cmd = [
            'monitor', 'log-analytics', 'workspace', 'create',
            '--resource-group', self.resource_group,
            '--workspace-name', workspace_name,
            '--location', self._get_location_for_resource('log_analytics')
        ]
        
        if self.tags:
            cmd.extend(['--tags', self.tags])
        
        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode != 0:
            return False, f"Failed to create Log Analytics workspace: {stderr}"
        
        # Get workspace ID
        returncode, stdout, stderr = run_az_command(
            [
                'monitor', 'log-analytics', 'workspace', 'show',
                '--resource-group', self.resource_group,
                '--workspace-name', workspace_name,
                '--query', 'customerId',
                '--output', 'tsv'
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        workspace_id = stdout.strip() if returncode == 0 else None
        
        self._mark_step_completed(step_name)
        self._save_resource('log_analytics', {
            'name': workspace_name,
            'id': workspace_id
        })
        
        return True, workspace_name
    
    def _get_log_analytics_workspace_id(self, workspace_name: str) -> Tuple[bool, str]:
        """Get the ID of an existing Log Analytics workspace."""
        returncode, stdout, stderr = run_az_command(
            [
                'monitor', 'log-analytics', 'workspace', 'show',
                '--resource-group', self.resource_group,
                '--workspace-name', workspace_name,
                '--query', 'customerId',
                '--output', 'tsv'
            ],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        
        if returncode == 0:
            workspace_id = stdout.strip()
            self._save_resource('log_analytics', {'name': workspace_name, 'id': workspace_id})
            return True, workspace_id
        else:
            return False, f"Could not retrieve ID for existing workspace '{workspace_name}': {stderr}"

    def create_application_insights(self, workspace_id: str) -> Tuple[bool, str]:
        """
        Create Application Insights.
        
        Args:
            workspace_id: Log Analytics workspace ID
            
        Returns:
            Tuple of (success, instrumentation_key)
        """
        step_name = "create_app_insights"
        app_insights_name = self.config['monitoring']['app_insights']

        # Idempotency check
        returncode, _, stderr = run_az_command(
            ['monitor', 'app-insights', 'component', 'show', '--app', app_insights_name, '--resource-group', self.resource_group],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        if returncode == 0:
            print_info(f"Application Insights '{app_insights_name}' already exists, skipping creation.")
            self._mark_step_completed(step_name)
            if 'app_insights' not in self.state['created_resources']:
                 return self._get_application_insights_key(app_insights_name)
            return True, self.state['created_resources']['app_insights'].get('key')
        
        print_info(f"Creating Application Insights '{app_insights_name}'...")
        
        cmd = [
            'monitor', 'app-insights', 'component', 'create',
            '--app', app_insights_name,
            '--location', self._get_location_for_resource('app_insights'),
            '--resource-group', self.resource_group,
            '--workspace', workspace_id
        ]
        
        if self.tags:
            cmd.extend(['--tags', self.tags])
        
        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode != 0:
            return False, f"Failed to create Application Insights: {stderr}"
        
        # Get instrumentation key
        returncode, stdout, stderr = run_az_command(
            [
                'monitor', 'app-insights', 'component', 'show',
                '--app', app_insights_name,
                '--resource-group', self.resource_group,
                '--query', 'instrumentationKey',
                '--output', 'tsv'
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        instrumentation_key = stdout.strip() if returncode == 0 else None
        
        self._mark_step_completed(step_name)
        self._save_resource('app_insights', {
            'name': app_insights_name,
            'key': instrumentation_key
        })

        return True, instrumentation_key

    def _get_application_insights_key(self, app_insights_name: str) -> Tuple[bool, str]:
        """Get the instrumentation key for an existing Application Insights instance."""
        returncode, stdout, stderr = run_az_command(
            [
                'monitor', 'app-insights', 'component', 'show',
                '--app', app_insights_name,
                '--resource-group', self.resource_group,
                '--query', 'instrumentationKey',
                '--output', 'tsv'
            ],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        
        if returncode == 0:
            instrumentation_key = stdout.strip()
            self._save_resource('app_insights', {'name': app_insights_name, 'key': instrumentation_key})
            return True, instrumentation_key
        else:
            return False, f"Could not retrieve key for existing Application Insights '{app_insights_name}': {stderr}"

    def create_postgresql_server(self) -> Tuple[bool, Dict[str, str]]:
        """
        Create Azure Database for PostgreSQL Flexible Server.

        Returns:
            Tuple of (success, database_info)
        """
        step_name = "create_postgresql"
        server_name = self.config['postgresql']['server_name']

        # Idempotency check
        returncode, _, stderr = run_az_command(
            ['postgres', 'flexible-server', 'show', '--name', server_name, '--resource-group', self.resource_group],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        if returncode == 0:
            print_info(f"PostgreSQL server '{server_name}' already exists.")
            self._mark_step_completed(step_name)
            
            # Check if credentials are in the state file
            if 'postgresql' not in self.state.get('created_resources', {}) or \
               'admin_password' not in self.state['created_resources']['postgresql']:
                
                print_warning(f"Credentials for '{server_name}' not found in state. Resetting admin password.")
                
                new_password = generate_password()
                
                # Update the password using Azure CLI
                update_cmd = [
                    'postgres', 'flexible-server', 'update',
                    '--resource-group', self.resource_group,
                    '--name', server_name,
                    '--admin-password', new_password
                ]
                
                update_returncode, _, update_stderr = run_az_command(
                    update_cmd, check=False, dry_run=self.dry_run, logger=self.logger
                )
                
                if update_returncode != 0:
                    return False, {'error': f"Failed to update password for existing PostgreSQL server: {update_stderr}"}
                
                # Since we don't know the original admin user, we'll have to assume it or fetch it.
                # For now, let's assume the user from config or a default, and save the new password.
                # A more robust solution might try to query the existing server for the admin user.
                admin_user = self.state.get('created_resources', {}).get('postgresql', {}).get('admin_user') or f"{self.project_name}admin"

                print_success(f"Password for user '{admin_user}' on server '{server_name}' has been reset.")

                # Reconstruct database info with the new password
                db_info = self.state.get('created_resources', {}).get('postgresql', {})
                db_info.update({
                    'admin_password': new_password,
                    'admin_user': admin_user,
                    'server_name': server_name,
                    'database_name': self.config['postgresql']['database_name'],
                    'host': f"{server_name}.postgres.database.azure.com",
                    'port': '5432'
                })
                db_info['connection_string'] = (
                    f"postgresql://{db_info['admin_user']}:{db_info['admin_password']}@"
                    f"{db_info['host']}:{db_info['port']}/{db_info['database_name']}?sslmode=require"
                )
                
                self._save_resource('postgresql', db_info)
                return True, db_info

            print_info("Credentials found in state, skipping creation.")
            return True, self.state['created_resources']['postgresql']
        admin_user = f"{self.project_name}admin{uuid.uuid4().hex[:6]}"
        admin_password = self.config['postgresql'].get('admin_password') or generate_password()
        database_name = self.config['postgresql']['database_name']
        sku = self.config['postgresql']['postgres_sku']
        tier = self.config['postgresql']['tier']
        version = self.config['postgresql']['version']
        storage_size = self.config['postgresql']['storage_size']

        print_info(f"Creating PostgreSQL server '{server_name}'...")
        print_warning("This may take 5-10 minutes...")

        cmd = [
            'postgres', 'flexible-server', 'create',
            '--resource-group', self.resource_group,
            '--name', server_name,
            '--location', self._get_location_for_resource('postgres_server'),
            '--admin-user', admin_user,
            '--admin-password', admin_password,
            '--sku-name', sku,
            '--tier', tier,
            '--version', version,
            '--storage-size', str(storage_size),
            '--public-access', '0.0.0.0-255.255.255.255',
            '--yes'
        ]

        if self.tags:
            cmd.extend(['--tags', self.tags])

        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode != 0:
            return False, {'error': f"Failed to create PostgreSQL server: {stderr}"}

        # Create database
        print_info(f"Creating database '{database_name}'...")

        returncode, stdout, stderr = run_az_command(
            [
                'postgres', 'flexible-server', 'db', 'create',
                '--resource-group', self.resource_group,
                '--server-name', server_name,
                '--database-name', database_name
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode != 0:
            print_warning(f"Failed to create database: {stderr}")

        # Construct connection string
        connection_string = (
            f"postgresql://{admin_user}:{admin_password}@"
            f"{server_name}.postgres.database.azure.com:5432/{database_name}?sslmode=require"
        )

        db_info = {
            'server_name': server_name,
            'database_name': database_name,
            'admin_user': admin_user,
            'admin_password': admin_password,
            'connection_string': connection_string,
            'host': f"{server_name}.postgres.database.azure.com",
            'port': '5432'
        }

        self._mark_step_completed(step_name)
        self._save_resource('postgresql', db_info)

        return True, db_info

    def create_redis_cache(self) -> Tuple[bool, Dict[str, str]]:
        """
        Create Azure Cache for Redis.

        Returns:
            Tuple of (success, redis_info)
        """
        step_name = "create_redis"
        redis_name = self.config['redis']['name']

        # Idempotency check
        returncode, _, stderr = run_az_command(
            ['redis', 'show', '--name', redis_name, '--resource-group', self.resource_group],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        if returncode == 0:
            print_info(f"Redis cache '{redis_name}' already exists, skipping creation.")
            self._mark_step_completed(step_name)
            if 'redis' not in self.state['created_resources']:
                return self._get_redis_keys(redis_name)
            return True, self.state['created_resources']['redis']
        sku = self.config['redis']['sku']
        vm_size = self.config['redis']['vm_size']

        print_info(f"Creating Redis cache '{redis_name}'...")
        print_warning("This may take 10-15 minutes...")

        cmd = [
            'redis', 'create',
            '--resource-group', self.resource_group,
            '--name', redis_name,
            '--location', self._get_location_for_resource('redis'),
            '--sku', sku,
            '--vm-size', vm_size,
        ]

        if self.tags:
            cmd.extend(['--tags', self.tags])

        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode != 0:
            return False, {'error': f"Failed to create Redis cache: {stderr}"}

        # Get Redis keys
        returncode, stdout, stderr = run_az_command(
            [
                'redis', 'list-keys',
                '--resource-group', self.resource_group,
                '--name', redis_name
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode == 0 and not self.dry_run:
            keys = json.loads(stdout)
            primary_key = keys.get('primaryKey')
        else:
            primary_key = None

        # Construct connection string
        connection_string = f"rediss://:{primary_key}@{redis_name}.redis.cache.windows.net:6380" if primary_key else None

        redis_info = {
            'name': redis_name,
            'host': f"{redis_name}.redis.cache.windows.net",
            'port': '6380',
            'primary_key': primary_key,
            'connection_string': connection_string
        }

        self._mark_step_completed(step_name)
        self._save_resource('redis', redis_info)

        return True, redis_info

    def _get_redis_keys(self, redis_name: str) -> Tuple[bool, Dict[str, str]]:
        """Get keys for an existing Redis cache."""
        returncode, stdout, stderr = run_az_command(
            ['redis', 'list-keys', '--resource-group', self.resource_group, '--name', redis_name],
            check=False, dry_run=self.dry_run, logger=self.logger
        )

        if returncode == 0 and not self.dry_run:
            keys = json.loads(stdout)
            primary_key = keys.get('primaryKey')
        else:
            primary_key = None
            if not self.dry_run:
                 return False, {'error': f"Could not retrieve keys for existing Redis cache '{redis_name}': {stderr}"}

        connection_string = f"rediss://:{primary_key}@{redis_name}.redis.cache.windows.net:6380" if primary_key else None
        redis_info = {
            'name': redis_name,
            'host': f"{redis_name}.redis.cache.windows.net",
            'port': '6380',
            'primary_key': primary_key,
            'connection_string': connection_string
        }
        self._save_resource('redis', redis_info)
        return True, redis_info

    def create_container_apps_environment(self, workspace_id: str) -> Tuple[bool, str]:
        """
        Create Container Apps Environment.

        Args:
            workspace_id: Log Analytics workspace ID

        Returns:
            Tuple of (success, environment_name)
        """
        step_name = "create_container_apps_env"
        env_name = self.config['container_apps']['environment_name']

        # Idempotency check
        returncode, _, stderr = run_az_command(
            ['containerapp', 'env', 'show', '--name', env_name, '--resource-group', self.resource_group],
            check=False, dry_run=self.dry_run, logger=self.logger
        )
        if returncode == 0:
            print_info(f"Container Apps environment '{env_name}' already exists, skipping creation.")
            self._mark_step_completed(step_name)
            self._save_resource('container_apps_env', {'name': env_name})
            return True, env_name

        print_info(f"Creating Container Apps environment '{env_name}'...")

        cmd = [
            'containerapp', 'env', 'create',
            '--name', env_name,
            '--resource-group', self.resource_group,
            '--location', self._get_location_for_resource('container_apps'),
            '--logs-workspace-id', workspace_id
        ]

        if self.tags:
            cmd.extend(['--tags', self.tags])

        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode == 0:
            self._mark_step_completed(step_name)
            self._save_resource('container_apps_env', {'name': env_name})
            return True, env_name
        else:
            return False, f"Failed to create Container Apps environment: {stderr}"

    def store_secret_in_keyvault(self, secret_name: str, secret_value: str) -> bool:
        """
        Store a secret in Azure Key Vault.

        Args:
            secret_name: Name of the secret
            secret_value: Value of the secret

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print_info(f"[DRY RUN] Would store secret '{secret_name}' in Key Vault")
            return True

        kv_name = self.config['key_vault']['name']

        returncode, stdout, stderr = run_az_command(
            [
                'keyvault', 'secret', 'set',
                '--vault-name', kv_name,
                '--name', secret_name,
                '--value', secret_value
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode == 0:
            print_success(f"Stored secret '{secret_name}' in Key Vault")
            return True
        else:
            print_error(f"Failed to store secret '{secret_name}': {stderr}")
            return False

