"""
Main deployment orchestrator for DraftGenie on Azure.
"""

import json
from typing import Dict, Any, Optional
import logging

from utils import (
    print_header, print_success, print_error, print_warning, print_info,
    print_step, generate_password, generate_secret, save_state,
    create_summary_file
)
from prerequisites import PrerequisitesChecker
from azure_resources import AzureResourceManager
from docker_builder import DockerBuilder
from container_apps import ContainerAppsDeployer


class DraftGenieDeployer:
    """Main orchestrator for DraftGenie Azure deployment."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        logger: logging.Logger,
        dry_run: bool = False,
        state: Dict[str, Any] = None
    ):
        """
        Initialize deployer.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
            dry_run: Dry run mode
            state: Deployment state
        """
        self.config = config
        self.logger = logger
        self.dry_run = dry_run
        self.state = state or {'completed_steps': [], 'created_resources': {}}
        
        # Initialize managers
        self.resource_manager = AzureResourceManager(config, logger, dry_run, self.state)
        self.prerequisites_checker = PrerequisitesChecker(logger, dry_run)
        
        # Will be initialized later
        self.docker_builder = None
        self.container_apps_deployer = None
        
        # Deployment info
        self.deployment_info = {
            'resource_group': config['azure']['resource_group'],
            'location': config['azure']['location'],
            'urls': {},
            'databases': {},
            'key_vault': config['key_vault']['name']
        }
    
    def deploy(self) -> bool:
        """
        Execute full deployment.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Check prerequisites
            if not self._step_check_prerequisites():
                return False
            
            # Step 2: Create resource group
            if not self._step_create_resource_group():
                return False
            
            # Step 3: Create monitoring infrastructure
            if not self._step_create_monitoring():
                return False
            
            # Step 4: Create container registry
            if not self._step_create_container_registry():
                return False
            
            # Step 5: Create Key Vault
            if not self._step_create_key_vault():
                return False
            
            # Step 6: Create databases
            if not self._step_create_databases():
                return False
            
            # Step 7: Store secrets
            if not self._step_store_secrets():
                return False
            
            # Step 8: Create Container Apps environment
            if not self._step_create_container_apps_env():
                return False
            
            # Step 9: Build and push Docker images
            if not self.config['deployment'].get('skip_build', False):
                if not self._step_build_and_push_images():
                    return False
            else:
                print_info("Skipping Docker image build (skip_build=true)")
            
            # Step 10: Deploy infrastructure services
            if not self._step_deploy_infrastructure_services():
                return False
            
            # Step 11: Deploy application services
            if not self._step_deploy_application_services():
                return False
            
            # Step 12: Run database migrations
            if not self.config['deployment'].get('skip_migrations', False):
                if not self._step_run_migrations():
                    return False
            else:
                print_info("Skipping database migrations (skip_migrations=true)")
            
            # Step 13: Verify deployment
            if not self._step_verify_deployment():
                return False
            
            # Step 14: Create summary
            self._create_deployment_summary()
            
            print_header("Deployment Complete!")
            print_success("DraftGenie has been successfully deployed to Azure")
            
            return True
            
        except KeyboardInterrupt:
            print_warning("\nDeployment interrupted by user")
            self._save_deployment_state()
            return False
        
        except Exception as e:
            print_error(f"Deployment failed: {str(e)}")
            self.logger.exception("Deployment error")
            self._save_deployment_state()
            return False
    
    def _step_check_prerequisites(self) -> bool:
        """Check all prerequisites."""
        print_step(1, 14, "Checking Prerequisites")
        
        if not self.prerequisites_checker.check_all():
            print_error("Prerequisites check failed")
            return False
        
        # Enable required providers
        success, message = self.prerequisites_checker.enable_required_providers()
        if success:
            print_success(message)
        
        return True
    
    def _step_create_resource_group(self) -> bool:
        """Create Azure resource group."""
        print_step(2, 14, "Creating Resource Group")
        
        success, message = self.resource_manager.create_resource_group()
        
        if success:
            print_success(message)
            self._save_deployment_state()
            return True
        else:
            print_error(message)
            return False
    
    def _step_create_monitoring(self) -> bool:
        """Create monitoring infrastructure."""
        print_step(3, 14, "Creating Monitoring Infrastructure")
        
        # Create Log Analytics workspace
        success, workspace_id = self.resource_manager.create_log_analytics_workspace()
        if not success:
            print_error(workspace_id)
            return False
        
        print_success(f"Log Analytics workspace created")
        
        # Create Application Insights
        success, instrumentation_key = self.resource_manager.create_application_insights(workspace_id)
        if not success:
            print_error(instrumentation_key)
            return False
        
        print_success(f"Application Insights created")
        
        self._save_deployment_state()
        return True
    
    def _step_create_container_registry(self) -> bool:
        """Create Azure Container Registry."""
        print_step(4, 14, "Creating Container Registry")
        
        success, registry_info = self.resource_manager.create_container_registry()
        
        if success:
            print_success(f"Container registry '{registry_info['name']}' created")
            self._save_deployment_state()
            return True
        else:
            print_error(registry_info.get('error', 'Unknown error'))
            return False
    
    def _step_create_key_vault(self) -> bool:
        """Create Azure Key Vault."""
        print_step(5, 14, "Creating Key Vault")
        
        success, kv_name = self.resource_manager.create_key_vault()
        
        if success:
            print_success(f"Key Vault '{kv_name}' created")
            self._save_deployment_state()
            return True
        else:
            print_error(kv_name)
            return False
    
    def _step_create_databases(self) -> bool:
        """Create database services."""
        print_step(6, 14, "Creating Database Services")
        
        # PostgreSQL
        print_info("Creating PostgreSQL server...")
        success, pg_info = self.resource_manager.create_postgresql_server()
        if not success:
            print_error(pg_info.get('error', 'Unknown error'))
            return False
        
        print_success(f"PostgreSQL server '{pg_info['server_name']}' created")
        self.deployment_info['databases']['postgresql'] = pg_info['connection_string']
        
        # Redis
        print_info("Creating Redis cache...")
        success, redis_info = self.resource_manager.create_redis_cache()
        if not success:
            print_error(redis_info.get('error', 'Unknown error'))
            return False
        
        print_success(f"Redis cache '{redis_info['name']}' created")
        self.deployment_info['databases']['redis'] = redis_info['connection_string']
        
        # MongoDB Atlas instructions
        if not self.config['mongodb'].get('connection_url'):
            print_warning("\nMongoDB Atlas Setup Required:")
            print_info("1. Go to https://www.mongodb.com/cloud/atlas")
            print_info("2. Create a free cluster (M0)")
            print_info("3. Create a database user")
            print_info("4. Whitelist your IP (or use 0.0.0.0/0 for testing)")
            print_info("5. Get the connection string")
            print_info("6. Update config.yaml with the MongoDB connection URL")
            print_info("7. Re-run deployment or manually add to Key Vault")
        
        self._save_deployment_state()
        return True
    
    def _step_store_secrets(self) -> bool:
        """Store secrets in Key Vault."""
        print_step(7, 14, "Storing Secrets in Key Vault")
        
        secrets_to_store = {}
        
        # Gemini API Key
        gemini_key = self.config['secrets'].get('gemini_api_key')
        if gemini_key:
            secrets_to_store['GEMINI-API-KEY'] = gemini_key
        else:
            print_error("Gemini API key is required. Please set it in config.yaml")
            return False
        
        # JWT Secret
        jwt_secret = self.config['secrets'].get('jwt_secret') or generate_secret()
        secrets_to_store['JWT-SECRET'] = jwt_secret
        
        # RabbitMQ password
        rabbitmq_password = self.config['secrets'].get('rabbitmq_password') or generate_password()
        secrets_to_store['RABBITMQ-PASSWORD'] = rabbitmq_password
        
        # Database credentials
        if 'postgresql' in self.state['created_resources']:
            pg_info = self.state['created_resources']['postgresql']
            secrets_to_store['POSTGRES-PASSWORD'] = pg_info['admin_password']
            secrets_to_store['DATABASE-URL'] = pg_info['connection_string']
        
        if 'redis' in self.state['created_resources']:
            redis_info = self.state['created_resources']['redis']
            if redis_info.get('connection_string'):
                secrets_to_store['REDIS-URL'] = redis_info['connection_string']
        
        # MongoDB URL
        mongodb_url = self.config['mongodb'].get('connection_url')
        if mongodb_url:
            secrets_to_store['MONGODB-URL'] = mongodb_url
        
        # Store all secrets
        for secret_name, secret_value in secrets_to_store.items():
            self.resource_manager.store_secret_in_keyvault(secret_name, secret_value)
        
        print_success(f"Stored {len(secrets_to_store)} secrets in Key Vault")
        
        self._save_deployment_state()
        return True
    
    def _step_create_container_apps_env(self) -> bool:
        """Create Container Apps environment."""
        print_step(8, 14, "Creating Container Apps Environment")
        
        workspace_id = self.state['created_resources']['log_analytics']['id']
        
        success, env_name = self.resource_manager.create_container_apps_environment(workspace_id)
        
        if success:
            print_success(f"Container Apps environment '{env_name}' created")
            self._save_deployment_state()
            return True
        else:
            print_error(env_name)
            return False
    
    def _save_deployment_state(self):
        """Save current deployment state."""
        if self.config['advanced'].get('save_state', True):
            state_file = self.config['advanced'].get('state_file', '.azure-deployment-state.json')
            save_state(self.state, state_file)
            self.logger.info(f"Deployment state saved to {state_file}")
    
    def _create_deployment_summary(self):
        """Create deployment summary file."""
        summary_file = "azure-deployment-summary.md"
        create_summary_file(self.deployment_info, summary_file)
        print_success(f"Deployment summary saved to {summary_file}")

    def _step_build_and_push_images(self) -> bool:
        """Build and push Docker images."""
        print_step(9, 14, "Building and Pushing Docker Images")

        registry_info = self.state['created_resources']['container_registry']

        self.docker_builder = DockerBuilder(
            self.config,
            registry_info,
            self.logger,
            self.dry_run
        )

        images = self.docker_builder.build_and_push_all()

        if len(images) == 0:
            print_error("Failed to build and push images")
            return False

        # Save image information
        self.state['created_resources']['images'] = images
        self._save_deployment_state()

        return True

    def _step_deploy_infrastructure_services(self) -> bool:
        """Deploy infrastructure services (RabbitMQ, Qdrant)."""
        print_step(10, 14, "Deploying Infrastructure Services")

        # Initialize Container Apps deployer
        registry_info = self.state['created_resources']['container_registry']
        env_name = self.state['created_resources']['container_apps_env']['name']

        self.container_apps_deployer = ContainerAppsDeployer(
            self.config,
            self.config['azure']['resource_group'],
            env_name,
            registry_info,
            self.logger,
            self.dry_run
        )

        # Deploy RabbitMQ
        print_info("Deploying RabbitMQ...")
        rabbitmq_config = self.config['services']['rabbitmq']
        rabbitmq_password = self.config['secrets'].get('rabbitmq_password') or generate_password()

        success, rabbitmq_url = self.container_apps_deployer.deploy_infrastructure_service(
            service_name=rabbitmq_config['name'],
            image=rabbitmq_config['image'],
            port=rabbitmq_config['port'],
            env_vars={
                'RABBITMQ_DEFAULT_USER': 'admin',
                'RABBITMQ_DEFAULT_PASS': rabbitmq_password
            },
            cpu=rabbitmq_config['cpu'],
            memory=rabbitmq_config['memory']
        )

        if not success:
            print_error("Failed to deploy RabbitMQ")
            return False

        print_success("RabbitMQ deployed")

        # Deploy Qdrant
        print_info("Deploying Qdrant...")
        qdrant_config = self.config['services']['qdrant']

        success, qdrant_url = self.container_apps_deployer.deploy_infrastructure_service(
            service_name=qdrant_config['name'],
            image=qdrant_config['image'],
            port=qdrant_config['port'],
            cpu=qdrant_config['cpu'],
            memory=qdrant_config['memory']
        )

        if not success:
            print_error("Failed to deploy Qdrant")
            return False

        print_success("Qdrant deployed")

        self._save_deployment_state()
        return True

    def _step_deploy_application_services(self) -> bool:
        """Deploy application services."""
        print_step(11, 14, "Deploying Application Services")

        # Get environment variables from state
        env_vars = self._build_environment_variables()

        # Get images
        images = self.state['created_resources'].get('images', {})

        # Deploy each service
        services_to_deploy = [
            ('speaker-service', self.config['services']['speaker_service']),
            ('draft-service', self.config['services']['draft_service']),
            ('rag-service', self.config['services']['rag_service']),
            ('evaluation-service', self.config['services']['evaluation_service']),
            ('api-gateway', self.config['services']['api_gateway']),
        ]

        for service_name, service_config in services_to_deploy:
            print_info(f"Deploying {service_name}...")

            image = images.get(service_name)
            if not image:
                print_error(f"Image not found for {service_name}")
                return False

            success, app_url = self.container_apps_deployer.deploy_container_app(
                app_name=service_config['name'],
                image=image,
                env_vars=env_vars,
                port=service_config['port'],
                cpu=service_config['cpu'],
                memory=service_config['memory'],
                min_replicas=service_config['min_replicas'],
                max_replicas=service_config['max_replicas'],
                ingress=service_config['ingress']
            )

            if not success:
                print_error(f"Failed to deploy {service_name}")
                return False

            print_success(f"Deployed {service_name}")

            if app_url:
                self.deployment_info['urls'][service_name] = app_url

        self._save_deployment_state()
        return True

    def _build_environment_variables(self) -> Dict[str, str]:
        """Build environment variables for application services."""
        env_vars = {}

        # Get database URLs from state
        pg_info = self.state['created_resources'].get('postgresql', {})
        redis_info = self.state['created_resources'].get('redis', {})

        # Database URLs
        if pg_info.get('connection_string'):
            env_vars['DATABASE_URL'] = pg_info['connection_string']

        if redis_info.get('connection_string'):
            env_vars['REDIS_URL'] = redis_info['connection_string']

        # MongoDB URL
        mongodb_url = self.config['mongodb'].get('connection_url')
        if mongodb_url:
            env_vars['MONGODB_URL'] = mongodb_url

        # Internal service URLs
        rabbitmq_name = self.config['services']['rabbitmq']['name']
        rabbitmq_password = self.config['secrets'].get('rabbitmq_password') or generate_password()
        env_vars['RABBITMQ_URL'] = f"amqp://admin:{rabbitmq_password}@{rabbitmq_name}:5672"

        qdrant_name = self.config['services']['qdrant']['name']
        env_vars['QDRANT_URL'] = f"http://{qdrant_name}:6333"

        # Service URLs
        for service_key in ['speaker_service', 'draft_service', 'rag_service', 'evaluation_service']:
            service_config = self.config['services'][service_key]
            service_name = service_config['name']
            service_port = service_config['port']
            env_var_name = f"{service_key.upper()}_URL"
            env_vars[env_var_name] = f"http://{service_name}:{service_port}"

        # Application config
        env_vars['NODE_ENV'] = 'production'
        env_vars['LOG_LEVEL'] = 'info'
        env_vars['CORS_ORIGIN'] = self.config['networking']['cors_origin']

        # Gemini API Key
        gemini_key = self.config['secrets'].get('gemini_api_key')
        if gemini_key:
            env_vars['GEMINI_API_KEY'] = gemini_key

        # JWT Secret
        jwt_secret = self.config['secrets'].get('jwt_secret') or generate_secret()
        env_vars['JWT_SECRET'] = jwt_secret

        return env_vars

    def _step_run_migrations(self) -> bool:
        """Run database migrations."""
        print_step(12, 14, "Running Database Migrations")

        print_info("Database migrations should be run manually or via CI/CD")
        print_info("Connect to the PostgreSQL database and run:")
        print_info("  cd services/speaker-service && npx prisma migrate deploy")

        # TODO: Implement automated migration execution
        # This would require executing commands in the container or using a job

        return True

    def _step_verify_deployment(self) -> bool:
        """Verify deployment."""
        print_step(13, 14, "Verifying Deployment")

        # Check if API Gateway is accessible
        api_gateway_url = self.deployment_info['urls'].get('api-gateway')

        if api_gateway_url:
            print_info(f"API Gateway URL: {api_gateway_url}")
            print_info(f"Health check: {api_gateway_url}/api/v1/health")
            print_info("Please verify the deployment by accessing the health check endpoint")
        else:
            print_warning("API Gateway URL not found")

        # List all deployed apps
        if self.container_apps_deployer:
            apps = self.container_apps_deployer.list_apps()
            print_info(f"Deployed {len(apps)} container apps")

        return True

