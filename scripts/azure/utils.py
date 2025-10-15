"""
Utility functions for Azure deployment automation.
"""

import os
import sys
import json
import yaml
import secrets
import string
import subprocess
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import logging
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def setup_logging(verbose: bool = False, log_file: str = "azure-deployment.log") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        verbose: Enable verbose logging
        log_file: Path to log file
        
    Returns:
        Configured logger instance
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logger
    logger = logging.getLogger('azure_deployment')
    logger.setLevel(log_level)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


def print_header(message: str):
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_step(step_num: int, total_steps: int, message: str):
    """Print a step message."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}[Step {step_num}/{total_steps}] {message}{Colors.ENDC}")


def generate_password(length: int = 32) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Password length
        
    Returns:
        Generated password
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_secret(length: int = 32) -> str:
    """
    Generate a secure random secret (base64-like).
    
    Args:
        length: Secret length
        
    Returns:
        Generated secret
    """
    return secrets.token_urlsafe(length)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def save_config(config: Dict[str, Any], config_path: str):
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save config file
    """
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def load_state(state_file: str) -> Dict[str, Any]:
    """
    Load deployment state from JSON file.
    
    Args:
        state_file: Path to state file
        
    Returns:
        State dictionary
    """
    if not os.path.exists(state_file):
        return {
            'completed_steps': [],
            'created_resources': {},
            'last_updated': None
        }
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    return state


def save_state(state: Dict[str, Any], state_file: str):
    """
    Save deployment state to JSON file.
    
    Args:
        state: State dictionary
        state_file: Path to state file
    """
    state['last_updated'] = datetime.now().isoformat()
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def run_command(
    command: List[str],
    check: bool = True,
    capture_output: bool = True,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
    input_data: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Tuple[int, str, str]:
    """
    Run a shell command.

    Args:
        command: Command and arguments as list
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout and stderr
        dry_run: Don't actually run the command
        logger: Logger instance
        input_data: Data to send to stdin

    Returns:
        Tuple of (return_code, stdout, stderr)

    Raises:
        subprocess.CalledProcessError: If command fails and check=True
    """
    cmd_str = ' '.join(command)

    if logger:
        logger.info(f"Executing command: {cmd_str}")

    if dry_run:
        print_info(f"[DRY RUN] Would run: {cmd_str}")
        return 0, "", ""

    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=capture_output,
            text=True,
            input=input_data,
            env=env
        )

        if logger:
            if result.stdout:
                logger.debug(f"stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"stderr: {result.stderr}")

        return result.returncode, result.stdout, result.stderr

    except subprocess.CalledProcessError as e:
        if logger:
            logger.error(f"Command failed: {cmd_str}")
            logger.error(f"Return code: {e.returncode}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")

        if check:
            raise

        return e.returncode, e.stdout, e.stderr


def run_az_command(
    args: List[str],
    check: bool = True,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None
) -> Tuple[int, str, str]:
    """
    Run an Azure CLI command.
    
    Args:
        args: Azure CLI arguments (without 'az' prefix)
        check: Raise exception on non-zero exit code
        dry_run: Don't actually run the command
        logger: Logger instance
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    command = ['az'] + args
    return run_command(command, check=check, capture_output=True, dry_run=dry_run, logger=logger)


def confirm_action(message: str, auto_approve: bool = False) -> bool:
    """
    Ask user for confirmation.
    
    Args:
        message: Confirmation message
        auto_approve: Auto-approve without asking
        
    Returns:
        True if confirmed, False otherwise
    """
    if auto_approve:
        return True
    
    response = input(f"{message} (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def validate_resource_name(name: str, resource_type: str) -> bool:
    """
    Validate Azure resource name.
    
    Args:
        name: Resource name
        resource_type: Type of resource (for specific validation rules)
        
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    # General rules
    if len(name) < 3 or len(name) > 63:
        return False
    
    # Specific rules for different resource types
    if resource_type == 'container_registry':
        # ACR names must be alphanumeric only
        return name.isalnum()
    
    elif resource_type == 'key_vault':
        # Key Vault names: alphanumeric and hyphens
        return all(c.isalnum() or c == '-' for c in name)
    
    elif resource_type == 'storage_account':
        # Storage account names: lowercase alphanumeric only
        return name.islower() and name.isalnum()
    
    # Default: alphanumeric and hyphens
    return all(c.isalnum() or c == '-' for c in name)


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    # Assume script is in scripts/azure/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    return project_root


def create_summary_file(deployment_info: Dict[str, Any], output_path: str):
    """
    Create a deployment summary file.
    
    Args:
        deployment_info: Deployment information dictionary
        output_path: Path to save summary file
    """
    with open(output_path, 'w') as f:
        f.write("# DraftGenie Azure Deployment Summary\n\n")
        f.write(f"**Deployment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Resource Group\n")
        f.write(f"- Name: {deployment_info.get('resource_group', 'N/A')}\n")
        f.write(f"- Location: {deployment_info.get('location', 'N/A')}\n\n")
        
        f.write("## Application URLs\n")
        if 'urls' in deployment_info:
            for service, url in deployment_info['urls'].items():
                f.write(f"- **{service}**: {url}\n")
        f.write("\n")
        
        f.write("## Database Connections\n")
        if 'databases' in deployment_info:
            for db, conn in deployment_info['databases'].items():
                f.write(f"- **{db}**: Stored in Key Vault\n")
        f.write("\n")
        
        f.write("## Secrets\n")
        f.write("All secrets are stored in Azure Key Vault.\n")
        f.write(f"Key Vault Name: {deployment_info.get('key_vault', 'N/A')}\n\n")
        
        f.write("## Next Steps\n")
        f.write("1. Verify deployment: `curl https://your-api-gateway-url/api/v1/health`\n")
        f.write("2. Set up custom domain (optional)\n")
        f.write("3. Configure monitoring alerts\n")
        f.write("4. Set up CI/CD pipeline\n")
        f.write("5. Review and optimize costs\n")

