"""
Docker image building and pushing to Azure Container Registry.

This module handles building Docker images with proper platform support (AMD64)
and pushing them to Azure Container Registry. It includes all fixes from the
successful shell script implementations.
"""

import os
import subprocess
import sys
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

        # Ensure Docker Desktop bin is in PATH (fix for credential helper)
        self._ensure_docker_desktop_in_path()

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

    def _ensure_docker_desktop_in_path(self):
        """
        Ensure Docker Desktop bin directory is in PATH.
        This fixes the docker-credential-desktop not found error.
        """
        docker_desktop_bin = "/Applications/Docker.app/Contents/Resources/bin"

        if os.path.exists(docker_desktop_bin):
            current_path = os.environ.get('PATH', '')
            if docker_desktop_bin not in current_path:
                os.environ['PATH'] = f"{docker_desktop_bin}:{current_path}"
                self.logger.info(f"Added Docker Desktop bin to PATH: {docker_desktop_bin}")
                print_info("Added Docker Desktop bin directory to PATH")
        else:
            self.logger.warning(f"Docker Desktop bin directory not found: {docker_desktop_bin}")
    
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
        Build Docker image for a service with AMD64 platform support.

        This method includes all fixes from successful shell scripts:
        - Builds for linux/amd64 platform (required for Azure Container Apps)
        - Uses Docker BuildKit for better logging
        - Includes proper error handling and logging

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
        print_info(f"  Platform: linux/amd64 (required for Azure Container Apps)")
        print_info(f"  Dockerfile: {dockerfile}")

        # Check if Dockerfile exists
        dockerfile_path = self.project_root / dockerfile
        if not dockerfile_path.exists():
            error_msg = f"Dockerfile not found: {dockerfile}"
            self.logger.error(error_msg)
            return False, error_msg

        # Build command with platform flag for AMD64
        # This is critical - Azure Container Apps requires linux/amd64 images
        cmd = [
            'docker', 'build',
            '--platform', 'linux/amd64',  # CRITICAL: Build for AMD64 architecture
            '-f', str(dockerfile_path),
            '-t', image_name
        ]

        # Add build args
        for key, value in build_args.items():
            cmd.extend(['--build-arg', f"{key}={value}"])

        # Add context
        context_path = self.project_root / context
        cmd.append(str(context_path))

        # Enable BuildKit for better logging and performance
        buildkit_env = os.environ.copy()
        buildkit_env["DOCKER_BUILDKIT"] = "1"

        # Log the build command
        self.logger.info(f"Build command: {' '.join(cmd)}")

        # Run build with detailed logging
        print_info(f"Running: docker build --platform linux/amd64 ...")
        returncode, stdout, stderr = run_command(
            cmd,
            check=False,
            dry_run=self.dry_run,
            logger=self.logger,
            env=buildkit_env
        )

        if returncode == 0:
            print_success(f"✓ Successfully built image: {image_name}")
            self.logger.info(f"Successfully built {service_name}")
            return True, image_name
        else:
            error_msg = f"Failed to build {service_name}: {stderr}"
            print_error(f"✗ Build failed for {service_name}")
            print_error(f"  Error: {stderr}")
            self.logger.error(error_msg)
            return False, image_name
    
    def push_image(self, image_name: str) -> Tuple[bool, str]:
        """
        Push Docker image to registry with detailed logging.

        Args:
            image_name: Full image name with registry

        Returns:
            Tuple of (success, message)
        """
        print_info(f"Pushing image to registry...")
        print_info(f"  Image: {image_name}")

        self.logger.info(f"Pushing image: {image_name}")

        returncode, stdout, stderr = run_command(
            ['docker', 'push', image_name],
            check=False,
            dry_run=self.dry_run,
            logger=self.logger
        )

        if returncode == 0:
            print_success(f"✓ Successfully pushed image: {image_name}")
            self.logger.info(f"Successfully pushed {image_name}")
            return True, f"Image pushed: {image_name}"
        else:
            error_msg = f"Failed to push image: {stderr}"
            print_error(f"✗ Push failed")
            print_error(f"  Error: {stderr}")
            self.logger.error(error_msg)
            return False, error_msg
    
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
        Build and push all service images with comprehensive error handling.

        This method includes all fixes from successful shell scripts:
        - Ensures Docker Desktop bin is in PATH
        - Builds images with --platform linux/amd64
        - Provides detailed logging for each step
        - Handles credential helper issues

        Args:
            tag: Image tag

        Returns:
            Dictionary mapping service names to image names
        """
        print_header("Building and Pushing Docker Images")
        print_info("Platform: linux/amd64 (required for Azure Container Apps)")
        print_info(f"Registry: {self.registry_info['login_server']}")
        print_info(f"Total services: {len(self.services)}")
        print_info("")

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
                    self.logger.info("Modified Docker config to remove credential helpers")

            # Login to registry first
            print_info("")
            print_info("=" * 80)
            print_info("Logging in to Azure Container Registry...")
            print_info("=" * 80)
            success, message = self.login_to_registry()
            if not success:
                print_error(message)
                self.logger.error(f"Registry login failed: {message}")
                return {}

            print_success(message)
            print_info("")

            # Build and push each service
            failed_services = []
            successful_services = []

            for i, service_name in enumerate(self.services.keys(), 1):
                print_info("=" * 80)
                print_step(i, len(self.services), f"Building and Pushing {service_name}")
                print_info("=" * 80)

                try:
                    success, image_name = self.build_and_push_service(service_name, tag)

                    if success:
                        images[service_name] = image_name
                        successful_services.append(service_name)
                        print_success(f"✓ {service_name} completed successfully")
                    else:
                        failed_services.append(service_name)
                        print_error(f"✗ {service_name} failed")
                        self.logger.error(f"Failed to build/push {service_name}")
                except Exception as e:
                    failed_services.append(service_name)
                    error_msg = f"Exception while building {service_name}: {str(e)}"
                    print_error(f"✗ {service_name} failed with exception")
                    print_error(f"  Error: {str(e)}")
                    self.logger.exception(error_msg)

                print_info("")

            # Summary
            print_info("=" * 80)
            print_header("Build and Push Summary")
            print_info("=" * 80)
            print_info(f"Total services: {len(self.services)}")
            print_info(f"Successful: {len(successful_services)}")
            print_info(f"Failed: {len(failed_services)}")

            if successful_services:
                print_success("\nSuccessfully built and pushed:")
                for service in successful_services:
                    print_success(f"  ✓ {service}")

            if failed_services:
                print_error("\nFailed services:")
                for service in failed_services:
                    print_error(f"  ✗ {service}")
                self.logger.error(f"Failed services: {', '.join(failed_services)}")
            else:
                print_success("\n🎉 All images built and pushed successfully!")
                self.logger.info("All images built and pushed successfully")

            print_info("=" * 80)

            return images

        except Exception as e:
            error_msg = f"Fatal error during build and push: {str(e)}"
            print_error(error_msg)
            self.logger.exception(error_msg)
            return {}

        finally:
            # Restore original Docker config
            if config_modified and original_config is not None:
                try:
                    with open(config_path, 'w') as f:
                        f.write(original_config)
                    print_info("Restored original Docker config.")
                    self.logger.info("Restored original Docker config")
                except Exception as e:
                    print_error(f"Failed to restore Docker config: {str(e)}")
                    self.logger.error(f"Failed to restore Docker config: {str(e)}")
    
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

