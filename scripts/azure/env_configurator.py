"""
Environment variable configuration for Azure Container Apps.

This module handles the configuration of environment variables for all
deployed container apps, ensuring they have the correct connection strings,
service URLs, and API keys to function properly.
"""

import json
from typing import Dict, Any, Optional, List, Tuple
import logging

from utils import (
    print_header, print_success, print_error, print_warning, print_info,
    run_az_command
)


class EnvVarConfigurator:
    """Configure environment variables for Azure Container Apps."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        resource_group: str,
        resource_manager: Any,  # AzureResourceManager instance
        logger: logging.Logger,
        dry_run: bool = False
    ):
        """
        Initialize environment variable configurator.
        
        Args:
            config: Configuration dictionary
            resource_group: Resource group name
            resource_manager: AzureResourceManager instance for accessing Key Vault
            logger: Logger instance
            dry_run: Dry run mode
        """
        self.config = config
        self.resource_group = resource_group
        self.resource_manager = resource_manager
        self.logger = logger
        self.dry_run = dry_run
    
    def configure_all_services(self, state: Dict[str, Any]) -> bool:
        """
        Configure environment variables for all services.
        
        Args:
            state: Deployment state containing resource information
            
        Returns:
            True if successful, False otherwise
        """
        print_header("Configuring Environment Variables for All Services")
        
        # Build common environment variables
        common_env_vars = self._build_common_env_vars(state)
        
        if not common_env_vars:
            print_error("Failed to build common environment variables")
            return False
        
        # Configure each service
        services_config = [
            ('api-gateway', self._build_api_gateway_env_vars),
            ('speaker-service', self._build_speaker_service_env_vars),
            ('draft-service', self._build_draft_service_env_vars),
            ('rag-service', self._build_rag_service_env_vars),
            ('eval-service', self._build_evaluation_service_env_vars),
        ]
        
        success_count = 0
        total_count = len(services_config)
        
        for service_name, build_env_func in services_config:
            print_info(f"\nConfiguring {service_name}...")
            
            # Check if service exists
            if not self._check_service_exists(service_name):
                print_warning(f"Service {service_name} not found, skipping")
                continue
            
            # Check if already configured
            if self._is_already_configured(service_name):
                print_info(f"Service {service_name} already has environment variables configured")
                success_count += 1
                continue
            
            # Build service-specific environment variables
            service_env_vars = build_env_func(common_env_vars, state)
            
            # Update container app
            if self._update_container_app_env_vars(service_name, service_env_vars):
                print_success(f"Configured {service_name}")
                success_count += 1
            else:
                print_error(f"Failed to configure {service_name}")
        
        # Summary
        print_info(f"\nConfigured {success_count}/{total_count} services")
        
        # Verify configuration
        if success_count > 0:
            self._verify_configuration()
        
        return success_count == total_count
    
    def _build_common_env_vars(self, state: Dict[str, Any]) -> Dict[str, str]:
        """
        Build common environment variables used by multiple services.
        
        Args:
            state: Deployment state
            
        Returns:
            Dictionary of common environment variables
        """
        env_vars = {}
        
        # Get secrets from Key Vault
        jwt_secret = self.resource_manager.get_secret_from_keyvault('JWT-SECRET')
        gemini_api_key = self.resource_manager.get_secret_from_keyvault('GEMINI-API-KEY')
        rabbitmq_password = self.resource_manager.get_secret_from_keyvault('RABBITMQ-PASSWORD')
        
        if not jwt_secret:
            print_error("JWT secret not found in Key Vault")
            return {}
        
        if not gemini_api_key:
            print_error("Gemini API key not found in Key Vault")
            return {}
        
        # Build database connection strings
        pg_info = state['created_resources'].get('postgresql', {})
        if pg_info.get('connection_string'):
            env_vars['DATABASE_URL'] = pg_info['connection_string']
        else:
            print_warning("PostgreSQL connection string not found in state")
        
        # Build Redis connection string
        redis_info = state['created_resources'].get('redis', {})
        if redis_info.get('connection_string'):
            env_vars['REDIS_URL'] = redis_info['connection_string']
        else:
            print_warning("Redis connection string not found in state")
        
        # Build RabbitMQ connection string
        rabbitmq_name = self.config['services']['rabbitmq']['name']
        if rabbitmq_password:
            env_vars['RABBITMQ_URL'] = f"amqp://admin:{rabbitmq_password}@{rabbitmq_name}:5672"
        else:
            print_warning("RabbitMQ password not found, using default")
            env_vars['RABBITMQ_URL'] = f"amqp://guest:guest@{rabbitmq_name}:5672"
        
        # Build Qdrant URL
        qdrant_name = self.config['services']['qdrant']['name']
        env_vars['QDRANT_URL'] = f"http://{qdrant_name}:6333"
        
        # Build service URLs
        env_info = state['created_resources'].get('container_apps_env', {})
        default_domain = env_info.get('default_domain', '')
        
        if default_domain:
            for service_key in ['speaker_service', 'draft_service', 'rag_service', 'evaluation_service']:
                service_config = self.config['services'][service_key]
                service_name = service_config['name']
                env_var_name = f"{service_key.upper()}_URL"
                env_vars[env_var_name] = f"http://{service_name}.internal.{default_domain}"
        else:
            print_warning("Default domain not found, service URLs may not work correctly")
        
        # Store common values
        env_vars['JWT_SECRET'] = jwt_secret
        env_vars['GEMINI_API_KEY'] = gemini_api_key
        env_vars['LOG_LEVEL'] = 'info'
        
        return env_vars
    
    def _build_api_gateway_env_vars(self, common_env_vars: Dict[str, str], state: Dict[str, Any]) -> Dict[str, str]:
        """Build environment variables for API Gateway."""
        return {
            'NODE_ENV': 'production',
            'PORT': '3000',
            'SPEAKER_SERVICE_URL': common_env_vars.get('SPEAKER_SERVICE_URL', 'http://speaker-service:3001'),
            'DRAFT_SERVICE_URL': common_env_vars.get('DRAFT_SERVICE_URL', 'http://draft-service:3002'),
            'RAG_SERVICE_URL': common_env_vars.get('RAG_SERVICE_URL', 'http://rag-service:3003'),
            'EVALUATION_SERVICE_URL': common_env_vars.get('EVALUATION_SERVICE_URL', 'http://eval-service:3004'),
            'JWT_SECRET': common_env_vars['JWT_SECRET'],
            'CORS_ORIGIN': self.config['networking'].get('cors_origin', '*'),
            'SWAGGER_ENABLED': 'true',
            'LOG_LEVEL': common_env_vars.get('LOG_LEVEL', 'info'),
        }
    
    def _build_speaker_service_env_vars(self, common_env_vars: Dict[str, str], state: Dict[str, Any]) -> Dict[str, str]:
        """Build environment variables for Speaker Service."""
        env_vars = {
            'NODE_ENV': 'production',
            'PORT': '3001',
            'JWT_SECRET': common_env_vars['JWT_SECRET'],
            'LOG_LEVEL': common_env_vars.get('LOG_LEVEL', 'info'),
        }
        
        if 'DATABASE_URL' in common_env_vars:
            env_vars['DATABASE_URL'] = common_env_vars['DATABASE_URL']
        
        if 'REDIS_URL' in common_env_vars:
            env_vars['REDIS_URL'] = common_env_vars['REDIS_URL']
        
        if 'RABBITMQ_URL' in common_env_vars:
            env_vars['RABBITMQ_URL'] = common_env_vars['RABBITMQ_URL']
        
        return env_vars
    
    def _build_draft_service_env_vars(self, common_env_vars: Dict[str, str], state: Dict[str, Any]) -> Dict[str, str]:
        """Build environment variables for Draft Service."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'PORT': '3002',
            'GEMINI_API_KEY': common_env_vars['GEMINI_API_KEY'],
            'LOG_LEVEL': common_env_vars.get('LOG_LEVEL', 'info'),
        }
        
        if 'DATABASE_URL' in common_env_vars:
            env_vars['DATABASE_URL'] = common_env_vars['DATABASE_URL']
        
        if 'QDRANT_URL' in common_env_vars:
            env_vars['QDRANT_URL'] = common_env_vars['QDRANT_URL']
        
        if 'RABBITMQ_URL' in common_env_vars:
            env_vars['RABBITMQ_URL'] = common_env_vars['RABBITMQ_URL']
        
        return env_vars
    
    def _build_rag_service_env_vars(self, common_env_vars: Dict[str, str], state: Dict[str, Any]) -> Dict[str, str]:
        """Build environment variables for RAG Service."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'PORT': '3003',
            'GEMINI_API_KEY': common_env_vars['GEMINI_API_KEY'],
            'LOG_LEVEL': common_env_vars.get('LOG_LEVEL', 'info'),
        }
        
        if 'DATABASE_URL' in common_env_vars:
            env_vars['DATABASE_URL'] = common_env_vars['DATABASE_URL']
        
        if 'QDRANT_URL' in common_env_vars:
            env_vars['QDRANT_URL'] = common_env_vars['QDRANT_URL']
        
        if 'SPEAKER_SERVICE_URL' in common_env_vars:
            env_vars['SPEAKER_SERVICE_URL'] = common_env_vars['SPEAKER_SERVICE_URL']
        
        if 'DRAFT_SERVICE_URL' in common_env_vars:
            env_vars['DRAFT_SERVICE_URL'] = common_env_vars['DRAFT_SERVICE_URL']
        
        return env_vars
    
    def _build_evaluation_service_env_vars(self, common_env_vars: Dict[str, str], state: Dict[str, Any]) -> Dict[str, str]:
        """Build environment variables for Evaluation Service."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'PORT': '3004',
            'GEMINI_API_KEY': common_env_vars['GEMINI_API_KEY'],
            'LOG_LEVEL': common_env_vars.get('LOG_LEVEL', 'info'),
        }

        if 'DATABASE_URL' in common_env_vars:
            env_vars['DATABASE_URL'] = common_env_vars['DATABASE_URL']

        if 'DRAFT_SERVICE_URL' in common_env_vars:
            env_vars['DRAFT_SERVICE_URL'] = common_env_vars['DRAFT_SERVICE_URL']

        return env_vars

    def _check_service_exists(self, service_name: str) -> bool:
        """
        Check if a container app exists.

        Args:
            service_name: Name of the service

        Returns:
            True if exists, False otherwise
        """
        returncode, stdout, stderr = run_az_command(
            [
                'containerapp', 'show',
                '--name', service_name,
                '--resource-group', self.resource_group,
                '--query', 'name',
                '--output', 'tsv'
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        return returncode == 0

    def _is_already_configured(self, service_name: str) -> bool:
        """
        Check if a service already has environment variables configured.

        Args:
            service_name: Name of the service

        Returns:
            True if already configured (has more than 2 env vars), False otherwise
        """
        if self.dry_run:
            return False

        returncode, stdout, stderr = run_az_command(
            [
                'containerapp', 'show',
                '--name', service_name,
                '--resource-group', self.resource_group,
                '--query', 'properties.template.containers[0].env | length(@)',
                '--output', 'tsv'
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode == 0:
            try:
                env_count = int(stdout.strip())
                # Consider configured if has more than 2 environment variables
                # (more than just JWT_SECRET)
                return env_count > 2
            except ValueError:
                return False

        return False

    def _update_container_app_env_vars(self, service_name: str, env_vars: Dict[str, str]) -> bool:
        """
        Update environment variables for a container app.

        Args:
            service_name: Name of the service
            env_vars: Environment variables to set

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print_info(f"[DRY RUN] Would update {service_name} with {len(env_vars)} environment variables")
            return True

        # Build the set-env-vars arguments
        env_args = []
        for key, value in env_vars.items():
            env_args.append(f"{key}={value}")

        # Update the container app
        cmd = [
            'containerapp', 'update',
            '--name', service_name,
            '--resource-group', self.resource_group,
            '--set-env-vars'
        ] + env_args + ['--output', 'none']

        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode == 0:
            self.logger.info(f"Updated environment variables for {service_name}")
            return True
        else:
            print_error(f"Failed to update {service_name}: {stderr}")
            return False

    def _verify_configuration(self):
        """Verify that all services have been configured."""
        print_info("\nVerifying environment variable configuration...")

        services = [
            'api-gateway',
            'speaker-service',
            'draft-service',
            'rag-service',
            'eval-service'
        ]

        for service_name in services:
            returncode, stdout, stderr = run_az_command(
                [
                    'containerapp', 'show',
                    '--name', service_name,
                    '--resource-group', self.resource_group,
                    '--query', 'properties.template.containers[0].env | length(@)',
                    '--output', 'tsv'
                ],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )

            if returncode == 0:
                try:
                    env_count = int(stdout.strip())
                    if env_count > 2:
                        print_success(f"  ✓ {service_name}: {env_count} environment variables")
                    else:
                        print_warning(f"  ⚠ {service_name}: Only {env_count} environment variables")
                except ValueError:
                    print_warning(f"  ⚠ {service_name}: Could not determine env var count")
            else:
                print_warning(f"  ⚠ {service_name}: Not found or not accessible")

