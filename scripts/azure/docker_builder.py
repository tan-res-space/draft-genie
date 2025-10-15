"""
Docker image building and pushing to Azure Container Registry.
"""

import os
from typing import Dict, Any, List, Tuple
import logging
from pathlib import Path

from utils import (
    print_header, print_success, print_error, print_warning, print_info,
    print_step, run_command, get_project_root
)


class DockerBuilder:
    """Build and push Docker images to Azure Container Registry."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        registry_info: Dict[str, str],
        logger: logging.Logger,
        dry_run: bool = False
    ):
        """
        Initialize Docker builder.
        
        Args:
            config: Configuration dictionary
            registry_info: Container registry information
            logger: Logger instance
            dry_run: Dry run mode
        """
        self.config = config
        self.registry_info = registry_info
        self.logger = logger
        self.dry_run = dry_run
        self.project_root = get_project_root()
        
        # Service definitions
        self.services = {
            'api-gateway': {
                'dockerfile': config['docker']['dockerfiles']['api_gateway'],
                'context': '.',
                'build_args': {}
            },
            'speaker-service': {
                'dockerfile': config['docker']['dockerfiles']['speaker_service'],
                'context': '.',
                'build_args': {}
            },
            'draft-service': {
                'dockerfile': config['docker']['dockerfiles']['draft_service'],
                'context': '.',
                'build_args': {}
            },
            'rag-service': {
                'dockerfile': config['docker']['dockerfiles']['rag_service'],
                'context': '.',
                'build_args': {}
            },
            'evaluation-service': {
                'dockerfile': config['docker']['dockerfiles']['evaluation_service'],
                'context': '.',
                'build_args': {}
            }
        }
    
    def login_to_registry(self) -> Tuple[bool, str]:
        """
        Login to Azure Container Registry using admin credentials.
        Temporarily disables Docker credential store to avoid issues with missing helpers.

        Returns:
            Tuple of (success, message)
        """
        if self.dry_run:
            print_info("Registry login skipped (dry run)")
            return True, "Registry login skipped (dry run)"

        registry_name = self.registry_info['name']
        login_server = self.registry_info['login_server']
        print_info(f"Logging in to Azure Container Registry '{registry_name}'...")

        # Step 1: Retrieve ACR credentials
        print_info("Retrieving ACR credentials...")
        returncode, stdout, stderr = run_command(
            ['az', 'acr', 'credential', 'show', '--name', registry_name],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode != 0:
            return False, f"Failed to retrieve ACR credentials: {stderr}"

        import json
        try:
            credentials = json.loads(stdout)
            username = credentials.get('username')
            password = credentials.get('passwords', [{}])[0].get('value')

            if not username or not password:
                return False, "Failed to parse ACR credentials from response."

        except (json.JSONDecodeError, IndexError) as e:
            return False, f"Failed to parse ACR credentials: {str(e)}"

        # Step 2: Login using Docker CLI with retrieved credentials
        print_info(f"Authenticating with Docker for registry '{login_server}'...")
        # Use Docker BuildKit for login
        buildkit_env = os.environ.copy()
        buildkit_env["DOCKER_BUILDKIT"] = "1"
        
        returncode, stdout, stderr = run_command(
            ['docker', 'login', login_server, '--username', username, '--password-stdin'],
            input_data=password,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger,
            env=buildkit_env
        )

        if returncode == 0:
            print_success(f"Successfully logged in to {registry_name}")
            return True, f"Logged in to {registry_name}"
        else:
            return False, f"Docker login failed: {stderr}"
    
    def build_image(self, service_name: str, tag: str = "latest") -> Tuple[bool, str]:
        """
        Build Docker image for a service.
        
        Args:
            service_name: Name of the service
            tag: Image tag
            
        Returns:
            Tuple of (success, image_name)
        """
        if service_name not in self.services:
            return False, f"Unknown service: {service_name}"
        
        service = self.services[service_name]
        dockerfile = service['dockerfile']
        context = service['context']
        build_args = service.get('build_args', {})
        
        # Construct image name
        registry_server = self.registry_info['login_server']
        image_name = f"{registry_server}/{service_name}:{tag}"
        
        print_info(f"Building image for {service_name}...")
        
        # Check if Dockerfile exists
        dockerfile_path = self.project_root / dockerfile
        if not dockerfile_path.exists():
            return False, f"Dockerfile not found: {dockerfile}"
        
        # Build command
        cmd = [
            'docker', 'build',
            '-f', str(dockerfile_path),
            '-t', image_name
        ]
        
        # Add build args
        for key, value in build_args.items():
            cmd.extend(['--build-arg', f"{key}={value}"])
        
        # Add context
        context_path = self.project_root / context
        cmd.append(str(context_path))
        
        # Enable BuildKit for more detailed logging
        buildkit_env = os.environ.copy()
        buildkit_env["DOCKER_BUILDKIT"] = "1"
        
        # Run build
        returncode, stdout, stderr = run_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger,
            env=buildkit_env
        )
        
        if returncode == 0:
            print_success(f"Built image: {image_name}")
            return True, image_name
        else:
            print_error(f"Failed to build image: {stderr}")
            return False, image_name
    
    def push_image(self, image_name: str) -> Tuple[bool, str]:
        """
        Push Docker image to registry.
        
        Args:
            image_name: Full image name with registry
            
        Returns:
            Tuple of (success, message)
        """
        print_info(f"Pushing image {image_name}...")
        
        returncode, stdout, stderr = run_command(
            ['docker', 'push', image_name],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )
        
        if returncode == 0:
            print_success(f"Pushed image: {image_name}")
            return True, f"Image pushed: {image_name}"
        else:
            print_error(f"Failed to push image: {stderr}")
            return False, f"Failed to push image: {stderr}"
    
    def build_and_push_service(self, service_name: str, tag: str = "latest") -> Tuple[bool, str]:
        """
        Build and push Docker image for a service.
        
        Args:
            service_name: Name of the service
            tag: Image tag
            
        Returns:
            Tuple of (success, image_name)
        """
        # Build image
        success, image_name = self.build_image(service_name, tag)
        if not success:
            return False, image_name
        
        # Push image
        success, message = self.push_image(image_name)
        if not success:
            return False, message
        
        return True, image_name
    
    def build_and_push_all(self, tag: str = "latest") -> Dict[str, str]:
        """
        Build and push all service images.
        
        Args:
            tag: Image tag
            
        Returns:
            Dictionary mapping service names to image names
        """
        print_header("Building and Pushing Docker Images")

        # Temporarily modify Docker config to remove credential helper
        config_path = os.path.expanduser("~/.docker/config.json")
        original_config = None
        config_modified = False
        images = {}
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    original_config = f.read()
                
                import json
                config_data = json.loads(original_config)
                
                # Remove credential store settings if they exist
                modified = False
                if 'credsStore' in config_data:
                    del config_data['credsStore']
                    modified = True
                if 'credHelpers' in config_data:
                    del config_data['credHelpers']
                    modified = True

                if modified:
                    with open(config_path, 'w') as f:
                        json.dump(config_data, f, indent=4)
                    config_modified = True
                    print_info("Temporarily modified Docker config to remove credential helper.")

            # Login to registry first
            success, message = self.login_to_registry()
            if not success:
                print_error(message)
                return {}
            
            print_success(message)
            
            # Build and push each service
            failed_services = []
            
            for i, service_name in enumerate(self.services.keys(), 1):
                print_step(i, len(self.services), f"Building {service_name}")
                
                success, image_name = self.build_and_push_service(service_name, tag)
                
                if success:
                    images[service_name] = image_name
                else:
                    failed_services.append(service_name)
                    print_error(f"Failed to build/push {service_name}")
            
            # Summary
            print("\n" + "=" * 80)
            print(f"Successfully built and pushed: {len(images)}/{len(self.services)} services")
            
            if failed_services:
                print_error(f"Failed services: {', '.join(failed_services)}")
            else:
                print_success("All images built and pushed successfully!")
            
            return images

        finally:
            # Restore original Docker config
            if config_modified and original_config is not None:
                with open(config_path, 'w') as f:
                    f.write(original_config)
                print_info("Restored original Docker config.")
    
    def get_image_name(self, service_name: str, tag: str = "latest") -> str:
        """
        Get the full image name for a service.
        
        Args:
            service_name: Name of the service
            tag: Image tag
            
        Returns:
            Full image name
        """
        registry_server = self.registry_info['login_server']
        return f"{registry_server}/{service_name}:{tag}"
    
    def verify_images_exist(self, images: Dict[str, str]) -> bool:
        """
        Verify that all images exist in the registry.
        
        Args:
            images: Dictionary mapping service names to image names
            
        Returns:
            True if all images exist, False otherwise
        """
        if self.dry_run:
            return True
        
        print_info("Verifying images in registry...")
        
        registry_name = self.registry_info['name']
        all_exist = True
        
        for service_name, image_name in images.items():
            # Extract repository and tag from image name
            # Format: registry.azurecr.io/service-name:tag
            parts = image_name.split('/')[-1].split(':')
            repository = parts[0]
            tag = parts[1] if len(parts) > 1 else 'latest'
            
            returncode, stdout, stderr = run_command(
                [
                    'az', 'acr', 'repository', 'show',
                    '--name', registry_name,
                    '--image', f"{repository}:{tag}"
                ],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode == 0:
                print_success(f"✓ {service_name}: {repository}:{tag}")
            else:
                print_error(f"✗ {service_name}: Image not found in registry")
                all_exist = False
        
        return all_exist


def build_and_push_images(
    config: Dict[str, Any],
    registry_info: Dict[str, str],
    logger: logging.Logger,
    dry_run: bool = False,
    tag: str = "latest"
) -> Dict[str, str]:
    """
    Build and push all Docker images.
    
    Args:
        config: Configuration dictionary
        registry_info: Container registry information
        logger: Logger instance
        dry_run: Dry run mode
        tag: Image tag
        
    Returns:
        Dictionary mapping service names to image names
    """
    builder = DockerBuilder(config, registry_info, logger, dry_run)
    return builder.build_and_push_all(tag)

