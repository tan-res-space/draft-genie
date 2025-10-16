"""
Azure Container Apps deployment.
"""

import json
import time
from typing import Dict, Any, List, Tuple, Optional
import logging

from utils import (
    print_header, print_success, print_error, print_warning, print_info,
    print_step, run_az_command
)


class ContainerAppsDeployer:
    """Deploy applications to Azure Container Apps."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        resource_group: str,
        environment_name: str,
        registry_info: Dict[str, str],
        logger: logging.Logger,
        dry_run: bool = False
    ):
        """
        Initialize Container Apps deployer.
        
        Args:
            config: Configuration dictionary
            resource_group: Resource group name
            environment_name: Container Apps environment name
            registry_info: Container registry information
            logger: Logger instance
            dry_run: Dry run mode
        """
        self.config = config
        self.resource_group = resource_group
        self.environment_name = environment_name
        self.registry_info = registry_info
        self.logger = logger
        self.dry_run = dry_run
    
    def deploy_container_app(
        self,
        app_name: str,
        image: str,
        env_vars: Dict[str, str],
        secrets: Dict[str, str] = None,
        port: int = 3000,
        cpu: float = 0.5,
        memory: str = "1Gi",
        min_replicas: int = 1,
        max_replicas: int = 3,
        ingress: str = "external"
    ) -> Tuple[bool, Optional[str]]:
        """
        Deploy a container app.
        
        Args:
            app_name: Application name
            image: Docker image name
            env_vars: Environment variables
            secrets: Secret environment variables
            port: Container port
            cpu: CPU allocation
            memory: Memory allocation
            min_replicas: Minimum replicas
            max_replicas: Maximum replicas
            ingress: Ingress type (external or internal)
            
        Returns:
            Tuple of (success, app_url)
        """
        print_info(f"Deploying container app '{app_name}'...")
        
        # Build environment variables string
        env_list = []
        for key, value in env_vars.items():
            env_list.extend(['--env-vars', f"{key}={value}"])
        
        # Build secrets string
        secret_list = []
        if secrets:
            for key, value in secrets.items():
                secret_list.extend(['--secrets', f"{key}={value}"])
                # Also add as env var referencing the secret
                env_list.extend(['--env-vars', f"{key}=secretref:{key}"])
        
        # Base command
        cmd = [
            'containerapp', 'create',
            '--name', app_name,
            '--resource-group', self.resource_group,
            '--environment', self.environment_name,
            '--image', image,
            '--target-port', str(port),
            '--cpu', str(cpu),
            '--memory', memory,
            '--min-replicas', str(min_replicas),
            '--max-replicas', str(max_replicas),
            '--ingress', ingress,
            '--registry-server', self.registry_info['login_server'],
            '--registry-username', self.registry_info.get('username', ''),
            '--registry-password', self.registry_info.get('password', '')
        ]
        
        # Add environment variables
        cmd.extend(env_list)
        
        # Add secrets
        cmd.extend(secret_list)
        
        # Execute deployment
        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode != 0:
            print_error(f"Failed to deploy {app_name}: {stderr}")
            return False, None
        
        # Get app URL if external ingress
        app_url = None
        if ingress == "external" and not self.dry_run:
            returncode, stdout, stderr = run_az_command(
                [
                    'containerapp', 'show',
                    '--name', app_name,
                    '--resource-group', self.resource_group,
                    '--query', 'properties.configuration.ingress.fqdn',
                    '--output', 'tsv'
                ],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode == 0:
                fqdn = stdout.strip()
                app_url = f"https://{fqdn}" if fqdn else None
        
        print_success(f"Deployed {app_name}" + (f" at {app_url}" if app_url else ""))
        
        return True, app_url
    
    def update_container_app(
        self,
        app_name: str,
        image: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        secrets: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str]:
        """
        Update an existing container app.
        
        Args:
            app_name: Application name
            image: New Docker image (optional)
            env_vars: New environment variables (optional)
            secrets: New secrets (optional)
            
        Returns:
            Tuple of (success, message)
        """
        print_info(f"Updating container app '{app_name}'...")
        
        cmd = [
            'containerapp', 'update',
            '--name', app_name,
            '--resource-group', self.resource_group
        ]
        
        if image:
            cmd.extend(['--image', image])
        
        if env_vars:
            for key, value in env_vars.items():
                cmd.extend(['--set-env-vars', f"{key}={value}"])
        
        if secrets:
            for key, value in secrets.items():
                cmd.extend(['--secrets', f"{key}={value}"])
        
        returncode, stdout, stderr = run_az_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode == 0:
            print_success(f"Updated {app_name}")
            return True, f"Updated {app_name}"
        else:
            print_error(f"Failed to update {app_name}: {stderr}")
            return False, f"Failed to update {app_name}: {stderr}"
    
    def deploy_infrastructure_service(
        self,
        service_name: str,
        image: str,
        port: int,
        env_vars: Dict[str, str] = None,
        cpu: float = 0.5,
        memory: str = "1Gi"
    ) -> Tuple[bool, Optional[str]]:
        """
        Deploy an infrastructure service (RabbitMQ, Qdrant).
        
        Args:
            service_name: Service name
            image: Docker image
            port: Container port
            env_vars: Environment variables
            cpu: CPU allocation
            memory: Memory allocation
            
        Returns:
            Tuple of (success, service_url)
        """
        return self.deploy_container_app(
            app_name=service_name,
            image=image,
            env_vars=env_vars or {},
            port=port,
            cpu=cpu,
            memory=memory,
            min_replicas=1,
            max_replicas=1,
            ingress="internal"
        )
    
    def get_app_url(self, app_name: str) -> Optional[str]:
        """
        Get the URL of a deployed container app.
        
        Args:
            app_name: Application name
            
        Returns:
            App URL or None
        """
        if self.dry_run:
            return f"https://{app_name}.example.com"
        
        returncode, stdout, stderr = run_az_command(
            [
                'containerapp', 'show',
                '--name', app_name,
                '--resource-group', self.resource_group,
                '--query', 'properties.configuration.ingress.fqdn',
                '--output', 'tsv'
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode == 0:
            fqdn = stdout.strip()
            return f"https://{fqdn}" if fqdn else None
        
        return None
    
    def get_internal_url(self, app_name: str) -> Optional[str]:
        """
        Get the internal URL of a container app.

        Args:
            app_name: Application name

        Returns:
            Internal URL with full FQDN or None
        """
        if self.dry_run:
            return f"http://{app_name}.internal.example.com"

        # Get the internal FQDN for the app
        returncode, stdout, stderr = run_az_command(
            [
                'containerapp', 'show',
                '--name', app_name,
                '--resource-group', self.resource_group,
                '--query', 'properties.configuration.ingress.fqdn',
                '--output', 'tsv'
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode == 0:
            fqdn = stdout.strip()
            # Internal apps have .internal. in their FQDN
            # Return with http:// (not https://) for internal communication
            return f"http://{fqdn}" if fqdn else None

        return None
    
    def wait_for_app_ready(self, app_name: str, timeout: int = 300) -> bool:
        """
        Wait for a container app to be ready.
        
        Args:
            app_name: Application name
            timeout: Timeout in seconds
            
        Returns:
            True if app is ready, False otherwise
        """
        if self.dry_run:
            return True
        
        print_info(f"Waiting for {app_name} to be ready...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            returncode, stdout, stderr = run_az_command(
                [
                    'containerapp', 'show',
                    '--name', app_name,
                    '--resource-group', self.resource_group,
                    '--query', 'properties.runningStatus',
                    '--output', 'tsv'
                ],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode == 0:
                status = stdout.strip()
                if status == 'Running':
                    print_success(f"{app_name} is ready")
                    return True
            
            time.sleep(10)
        
        print_warning(f"{app_name} did not become ready within {timeout} seconds")
        return False
    
    def list_apps(self) -> List[Dict[str, Any]]:
        """
        List all container apps in the environment.
        
        Returns:
            List of app information dictionaries
        """
        if self.dry_run:
            return []
        
        returncode, stdout, stderr = run_az_command(
            [
                'containerapp', 'list',
                '--resource-group', self.resource_group,
                '--output', 'json'
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode == 0:
            return json.loads(stdout)
        
        return []
    
    def delete_app(self, app_name: str) -> bool:
        """
        Delete a container app.
        
        Args:
            app_name: Application name
            
        Returns:
            True if successful, False otherwise
        """
        print_info(f"Deleting container app '{app_name}'...")
        
        returncode, stdout, stderr = run_az_command(
            [
                'containerapp', 'delete',
                '--name', app_name,
                '--resource-group', self.resource_group,
                '--yes'
            ],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode == 0:
            print_success(f"Deleted {app_name}")
            return True
        else:
            print_error(f"Failed to delete {app_name}: {stderr}")
            return False

