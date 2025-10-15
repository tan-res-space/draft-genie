"""
Prerequisites checker for Azure deployment.
"""

import subprocess
import sys
from typing import Dict, List, Tuple
import logging

from utils import (
    print_header, print_success, print_error, print_warning, print_info,
    run_command, run_az_command
)


class PrerequisitesChecker:
    """Check all prerequisites for Azure deployment."""
    
    def __init__(self, logger: logging.Logger, dry_run: bool = False):
        """
        Initialize prerequisites checker.
        
        Args:
            logger: Logger instance
            dry_run: Dry run mode
        """
        self.logger = logger
        self.dry_run = dry_run
        self.checks_passed = []
        self.checks_failed = []
    
    def check_all(self) -> bool:
        """
        Run all prerequisite checks.
        
        Returns:
            True if all checks passed, False otherwise
        """
        print_header("Checking Prerequisites")
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Azure CLI", self.check_azure_cli),
            ("Azure Login", self.check_azure_login),
            ("Docker", self.check_docker),
            ("Git", self.check_git),
        ]
        
        for check_name, check_func in checks:
            print_info(f"Checking {check_name}...")
            
            try:
                success, message = check_func()
                
                if success:
                    print_success(message)
                    self.checks_passed.append(check_name)
                else:
                    print_error(message)
                    self.checks_failed.append(check_name)
                    
            except Exception as e:
                print_error(f"Error checking {check_name}: {str(e)}")
                self.checks_failed.append(check_name)
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"Checks Passed: {len(self.checks_passed)}/{len(checks)}")
        
        if self.checks_failed:
            print_error(f"Failed checks: {', '.join(self.checks_failed)}")
            return False
        else:
            print_success("All prerequisite checks passed!")
            return True
    
    def check_python_version(self) -> Tuple[bool, str]:
        """
        Check Python version (requires 3.8+).
        
        Returns:
            Tuple of (success, message)
        """
        version = sys.version_info
        
        if version.major >= 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro} (OK)"
        else:
            return False, f"Python {version.major}.{version.minor}.{version.micro} (Requires 3.8+)"
    
    def check_azure_cli(self) -> Tuple[bool, str]:
        """
        Check if Azure CLI is installed.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            returncode, stdout, stderr = run_command(
                ['az', '--version'],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode == 0:
                # Extract version from output
                version_line = stdout.split('\n')[0]
                return True, f"Azure CLI installed: {version_line}"
            else:
                return False, "Azure CLI not found. Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
                
        except FileNotFoundError:
            return False, "Azure CLI not found. Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    
    def check_azure_login(self) -> Tuple[bool, str]:
        """
        Check if user is logged in to Azure.
        
        Returns:
            Tuple of (success, message)
        """
        if self.dry_run:
            return True, "Azure login check skipped (dry run)"
        
        try:
            returncode, stdout, stderr = run_az_command(
                ['account', 'show'],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode == 0:
                # Parse account info
                import json
                account = json.loads(stdout)
                user = account.get('user', {}).get('name', 'Unknown')
                subscription = account.get('name', 'Unknown')
                
                return True, f"Logged in as {user} (Subscription: {subscription})"
            else:
                return False, "Not logged in to Azure. Run: az login"
                
        except Exception as e:
            return False, f"Error checking Azure login: {str(e)}"
    
    def check_docker(self) -> Tuple[bool, str]:
        """
        Check if Docker is installed and running.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if Docker is installed
            returncode, stdout, stderr = run_command(
                ['docker', '--version'],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode != 0:
                return False, "Docker not found. Install from: https://www.docker.com/products/docker-desktop"
            
            version = stdout.strip()
            
            # Check if Docker daemon is running
            returncode, stdout, stderr = run_command(
                ['docker', 'info'],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode != 0:
                return False, f"{version} (Docker daemon not running. Please start Docker Desktop)"
            
            return True, f"{version} (Running)"
            
        except FileNotFoundError:
            return False, "Docker not found. Install from: https://www.docker.com/products/docker-desktop"
    
    def check_git(self) -> Tuple[bool, str]:
        """
        Check if Git is installed.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            returncode, stdout, stderr = run_command(
                ['git', '--version'],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode == 0:
                version = stdout.strip()
                return True, f"{version}"
            else:
                return False, "Git not found. Install from: https://git-scm.com/"
                
        except FileNotFoundError:
            return False, "Git not found. Install from: https://git-scm.com/"
    
    def check_subscription(self, subscription_id: str = None) -> Tuple[bool, str]:
        """
        Check and optionally set Azure subscription.
        
        Args:
            subscription_id: Subscription ID to set (optional)
            
        Returns:
            Tuple of (success, message)
        """
        if self.dry_run:
            return True, "Subscription check skipped (dry run)"
        
        try:
            if subscription_id:
                # Set subscription
                returncode, stdout, stderr = run_az_command(
                    ['account', 'set', '--subscription', subscription_id],
                    check=False,
                    dry_run=self.dry_run,
                    logger=self.logger
                )
                
                if returncode != 0:
                    return False, f"Failed to set subscription: {stderr}"
            
            # Get current subscription
            returncode, stdout, stderr = run_az_command(
                ['account', 'show'],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode == 0:
                import json
                account = json.loads(stdout)
                subscription_name = account.get('name', 'Unknown')
                subscription_id = account.get('id', 'Unknown')
                
                return True, f"Using subscription: {subscription_name} ({subscription_id})"
            else:
                return False, "Failed to get subscription info"
                
        except Exception as e:
            return False, f"Error checking subscription: {str(e)}"
    
    def list_subscriptions(self) -> List[Dict[str, str]]:
        """
        List all available Azure subscriptions.
        
        Returns:
            List of subscription dictionaries
        """
        if self.dry_run:
            return []
        
        try:
            returncode, stdout, stderr = run_az_command(
                ['account', 'list', '--output', 'json'],
                check=False,
                dry_run=self.dry_run,
                logger=self.logger
            )
            
            if returncode == 0:
                import json
                subscriptions = json.loads(stdout)
                return [
                    {
                        'id': sub.get('id'),
                        'name': sub.get('name'),
                        'state': sub.get('state'),
                        'isDefault': sub.get('isDefault', False)
                    }
                    for sub in subscriptions
                ]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error listing subscriptions: {str(e)}")
            return []
    
    def enable_required_providers(self) -> Tuple[bool, str]:
        """
        Enable required Azure resource providers.
        
        Returns:
            Tuple of (success, message)
        """
        if self.dry_run:
            return True, "Provider registration skipped (dry run)"
        
        providers = [
            'Microsoft.ContainerRegistry',
            'Microsoft.App',
            'Microsoft.OperationalInsights',
            'Microsoft.Insights',
            'Microsoft.DBforPostgreSQL',
            'Microsoft.Cache',
            'Microsoft.KeyVault',
        ]
        
        print_info("Registering required resource providers...")
        
        for provider in providers:
            try:
                returncode, stdout, stderr = run_az_command(
                    ['provider', 'register', '--namespace', provider],
                    check=False,
                    dry_run=self.dry_run,
                    logger=self.logger
                )
                
                if returncode == 0:
                    print_success(f"Registered {provider}")
                else:
                    print_warning(f"Failed to register {provider}: {stderr}")
                    
            except Exception as e:
                print_warning(f"Error registering {provider}: {str(e)}")
        
        return True, "Resource providers registered (may take a few minutes to complete)"


def check_prerequisites(logger: logging.Logger, dry_run: bool = False) -> bool:
    """
    Check all prerequisites for deployment.
    
    Args:
        logger: Logger instance
        dry_run: Dry run mode
        
    Returns:
        True if all checks passed, False otherwise
    """
    checker = PrerequisitesChecker(logger, dry_run)
    return checker.check_all()

