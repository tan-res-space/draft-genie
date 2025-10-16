#!/usr/bin/env python3
"""
Azure Deployment Testing Script

This script comprehensively tests all deployed services in Azure Container Apps,
including health checks, connectivity tests, and service integration tests.

Usage:
    python scripts/azure/test_azure_deployment.py [options]

Options:
    --config PATH       Path to configuration file (default: scripts/azure/config.yaml)
    --verbose          Enable verbose logging
    --report PATH      Save test report to file (default: azure-test-report.json)
    --skip-logs        Skip fetching logs for failed services
    --help             Show this help message
"""

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import time

# Add azure module to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from utils import (
        setup_logging, load_config,
        print_header, print_success, print_error, print_warning, print_info,
        run_az_command
    )
except ImportError:
    print("Error: Could not import Azure utilities. Make sure you're running from the correct directory.")
    sys.exit(1)

# Try to import requests for HTTP testing
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: 'requests' library not found. HTTP tests will use curl instead.")


class AzureServiceTester:
    """Test deployed Azure services."""
    
    def __init__(self, config: dict, logger, verbose: bool = False):
        """
        Initialize the tester.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
            verbose: Enable verbose output
        """
        self.config = config
        self.logger = logger
        self.verbose = verbose
        self.resource_group = config['azure']['resource_group']
        self.environment_name = config['container_apps']['environment_name']
        
        # Test results
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'resource_group': self.resource_group,
            'environment': self.environment_name,
            'services': {},
            'infrastructure': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def run_all_tests(self) -> bool:
        """
        Run all tests.
        
        Returns:
            True if all tests passed, False otherwise
        """
        print_header("Azure Deployment Testing")
        
        # Pre-flight checks
        if not self._check_prerequisites():
            return False
        
        # Test infrastructure
        print_header("Testing Infrastructure Services")
        self._test_infrastructure()
        
        # Test container apps
        print_header("Testing Container Apps")
        self._test_container_apps()
        
        # Test service connectivity
        print_header("Testing Service Connectivity")
        self._test_service_connectivity()
        
        # Test API endpoints
        print_header("Testing API Endpoints")
        self._test_api_endpoints()
        
        # Print summary
        self._print_summary()
        
        return self.results['summary']['failed'] == 0
    
    def _check_prerequisites(self) -> bool:
        """Check prerequisites."""
        print_info("Checking prerequisites...")
        
        # Check Azure CLI
        returncode, _, _ = run_az_command(['--version'], check=False, logger=self.logger)
        if returncode != 0:
            print_error("Azure CLI is not installed or not in PATH")
            return False
        print_success("Azure CLI is available")
        
        # Check Azure login
        returncode, _, _ = run_az_command(['account', 'show'], check=False, logger=self.logger)
        if returncode != 0:
            print_error("Not logged in to Azure. Please run 'az login'")
            return False
        print_success("Logged in to Azure")
        
        return True
    
    def _test_infrastructure(self):
        """Test infrastructure services."""
        
        # Test PostgreSQL
        self._test_postgresql()
        
        # Test Redis
        self._test_redis()
        
        # Test Key Vault
        self._test_key_vault()
        
        # Test Container Registry
        self._test_container_registry()
        
        # Test Container Apps Environment
        self._test_container_environment()
    
    def _test_postgresql(self):
        """Test PostgreSQL database."""
        print_info("Testing PostgreSQL...")
        
        server_name = self.config['postgresql']['server_name']
        
        returncode, stdout, stderr = run_az_command([
            'postgres', 'flexible-server', 'show',
            '--name', server_name,
            '--resource-group', self.resource_group,
            '--query', 'state',
            '--output', 'tsv'
        ], check=False, logger=self.logger)
        
        if returncode == 0 and stdout.strip() == 'Ready':
            print_success(f"PostgreSQL server '{server_name}' is Ready")
            self.results['infrastructure']['postgresql'] = {
                'status': 'passed',
                'state': 'Ready',
                'server': server_name
            }
            self.results['summary']['passed'] += 1
        else:
            print_error(f"PostgreSQL server '{server_name}' is not ready")
            self.results['infrastructure']['postgresql'] = {
                'status': 'failed',
                'state': stdout.strip() if returncode == 0 else 'unknown',
                'server': server_name,
                'error': stderr
            }
            self.results['summary']['failed'] += 1
        
        self.results['summary']['total_tests'] += 1
    
    def _test_redis(self):
        """Test Redis cache."""
        print_info("Testing Redis...")
        
        redis_name = self.config['redis']['name']
        
        returncode, stdout, stderr = run_az_command([
            'redis', 'show',
            '--name', redis_name,
            '--resource-group', self.resource_group,
            '--query', 'provisioningState',
            '--output', 'tsv'
        ], check=False, logger=self.logger)
        
        if returncode == 0 and stdout.strip() == 'Succeeded':
            print_success(f"Redis cache '{redis_name}' is running")
            self.results['infrastructure']['redis'] = {
                'status': 'passed',
                'state': 'Succeeded',
                'name': redis_name
            }
            self.results['summary']['passed'] += 1
        else:
            print_error(f"Redis cache '{redis_name}' is not ready")
            self.results['infrastructure']['redis'] = {
                'status': 'failed',
                'state': stdout.strip() if returncode == 0 else 'unknown',
                'name': redis_name,
                'error': stderr
            }
            self.results['summary']['failed'] += 1
        
        self.results['summary']['total_tests'] += 1
    
    def _test_key_vault(self):
        """Test Key Vault."""
        print_info("Testing Key Vault...")
        
        kv_name = self.config['key_vault']['name']
        
        returncode, stdout, stderr = run_az_command([
            'keyvault', 'show',
            '--name', kv_name,
            '--resource-group', self.resource_group,
            '--query', 'properties.provisioningState',
            '--output', 'tsv'
        ], check=False, logger=self.logger)
        
        if returncode == 0 and stdout.strip() == 'Succeeded':
            print_success(f"Key Vault '{kv_name}' is active")
            self.results['infrastructure']['key_vault'] = {
                'status': 'passed',
                'state': 'Succeeded',
                'name': kv_name
            }
            self.results['summary']['passed'] += 1
        else:
            print_error(f"Key Vault '{kv_name}' is not ready")
            self.results['infrastructure']['key_vault'] = {
                'status': 'failed',
                'state': stdout.strip() if returncode == 0 else 'unknown',
                'name': kv_name,
                'error': stderr
            }
            self.results['summary']['failed'] += 1
        
        self.results['summary']['total_tests'] += 1
    
    def _test_container_registry(self):
        """Test Container Registry."""
        print_info("Testing Container Registry...")
        
        acr_name = self.config['container_registry']['name']
        
        returncode, stdout, stderr = run_az_command([
            'acr', 'show',
            '--name', acr_name,
            '--resource-group', self.resource_group,
            '--query', 'provisioningState',
            '--output', 'tsv'
        ], check=False, logger=self.logger)
        
        if returncode == 0 and stdout.strip() == 'Succeeded':
            print_success(f"Container Registry '{acr_name}' is active")
            self.results['infrastructure']['container_registry'] = {
                'status': 'passed',
                'state': 'Succeeded',
                'name': acr_name
            }
            self.results['summary']['passed'] += 1
        else:
            print_error(f"Container Registry '{acr_name}' is not ready")
            self.results['infrastructure']['container_registry'] = {
                'status': 'failed',
                'state': stdout.strip() if returncode == 0 else 'unknown',
                'name': acr_name,
                'error': stderr
            }
            self.results['summary']['failed'] += 1
        
        self.results['summary']['total_tests'] += 1

    def _test_container_environment(self):
        """Test Container Apps Environment."""
        print_info("Testing Container Apps Environment...")

        returncode, stdout, stderr = run_az_command([
            'containerapp', 'env', 'show',
            '--name', self.environment_name,
            '--resource-group', self.resource_group,
            '--query', 'properties.provisioningState',
            '--output', 'tsv'
        ], check=False, logger=self.logger)

        if returncode == 0 and stdout.strip() == 'Succeeded':
            print_success(f"Container Apps Environment '{self.environment_name}' is ready")
            self.results['infrastructure']['container_environment'] = {
                'status': 'passed',
                'state': 'Succeeded',
                'name': self.environment_name
            }
            self.results['summary']['passed'] += 1
        else:
            print_error(f"Container Apps Environment '{self.environment_name}' is not ready")
            self.results['infrastructure']['container_environment'] = {
                'status': 'failed',
                'state': stdout.strip() if returncode == 0 else 'unknown',
                'name': self.environment_name,
                'error': stderr
            }
            self.results['summary']['failed'] += 1

        self.results['summary']['total_tests'] += 1

    def _test_container_apps(self):
        """Test all container apps."""

        services = self.config.get('services', {})

        for _, service_config in services.items():
            service_name = service_config.get('name')
            if service_name:
                self._test_container_app(service_name, service_config)

    def _test_container_app(self, app_name: str, config: dict):
        """Test a single container app."""
        print_info(f"Testing container app '{app_name}'...")

        result = {
            'name': app_name,
            'tests': {}
        }

        # Check if app exists
        returncode, stdout, stderr = run_az_command([
            'containerapp', 'show',
            '--name', app_name,
            '--resource-group', self.resource_group,
            '--output', 'json'
        ], check=False, logger=self.logger)

        if returncode != 0:
            print_error(f"Container app '{app_name}' not found")
            result['status'] = 'failed'
            result['error'] = 'App not found'
            self.results['services'][app_name] = result
            self.results['summary']['failed'] += 1
            self.results['summary']['total_tests'] += 1
            return

        try:
            app_info = json.loads(stdout)
        except json.JSONDecodeError:
            print_error(f"Failed to parse app info for '{app_name}'")
            result['status'] = 'failed'
            result['error'] = 'Failed to parse app info'
            self.results['services'][app_name] = result
            self.results['summary']['failed'] += 1
            self.results['summary']['total_tests'] += 1
            return

        # Check running status
        running_status = app_info.get('properties', {}).get('runningStatus', 'Unknown')
        result['running_status'] = running_status

        if running_status == 'Running':
            print_success(f"  ✓ '{app_name}' is Running")
            result['tests']['running'] = 'passed'
        else:
            print_error(f"  ✗ '{app_name}' status: {running_status}")
            result['tests']['running'] = 'failed'

        # Check replicas
        returncode, stdout, stderr = run_az_command([
            'containerapp', 'replica', 'list',
            '--name', app_name,
            '--resource-group', self.resource_group,
            '--query', 'length(@)',
            '--output', 'tsv'
        ], check=False, logger=self.logger)

        if returncode == 0:
            replica_count = int(stdout.strip()) if stdout.strip() else 0
            result['replica_count'] = replica_count
            print_info(f"  ℹ '{app_name}' has {replica_count} replica(s)")

            if replica_count > 0:
                result['tests']['replicas'] = 'passed'
            else:
                result['tests']['replicas'] = 'failed'
                print_warning(f"  ⚠ '{app_name}' has no running replicas")

        # Get URL if external ingress
        ingress = app_info.get('properties', {}).get('configuration', {}).get('ingress', {})
        if ingress:
            fqdn = ingress.get('fqdn')
            if fqdn:
                url = f"https://{fqdn}"
                result['url'] = url
                print_info(f"  ℹ URL: {url}")

            # Check environment variables
            containers = app_info.get('properties', {}).get('template', {}).get('containers', [])
            if containers:
                env_vars = containers[0].get('env', [])
                result['env_var_count'] = len(env_vars)
                print_info(f"  ℹ Environment variables: {len(env_vars)}")

                if len(env_vars) > 1:  # More than just JWT_SECRET
                    result['tests']['env_vars'] = 'passed'
                else:
                    result['tests']['env_vars'] = 'warning'
                    print_warning(f"  ⚠ '{app_name}' has minimal environment variables")

        # Determine overall status
        if all(v == 'passed' for v in result['tests'].values()):
            result['status'] = 'passed'
            self.results['summary']['passed'] += 1
        elif any(v == 'failed' for v in result['tests'].values()):
            result['status'] = 'failed'
            self.results['summary']['failed'] += 1
        else:
            result['status'] = 'warning'
            self.results['summary']['warnings'] += 1

        self.results['services'][app_name] = result
        self.results['summary']['total_tests'] += 1

    def _test_service_connectivity(self):
        """Test service-to-service connectivity."""
        print_info("Testing service connectivity...")

        # Get API Gateway URL
        api_gateway_url = self._get_service_url('api-gateway')

        if not api_gateway_url:
            print_warning("API Gateway URL not found, skipping connectivity tests")
            return

        # Test API Gateway health
        health_url = f"{api_gateway_url}/api/v1/health"
        self._test_http_endpoint(
            'api-gateway-health',
            health_url,
            expected_status=200,
            description="API Gateway Health Check"
        )

        # Test backend services health through API Gateway
        services_health_url = f"{api_gateway_url}/api/v1/health/services"
        self._test_http_endpoint(
            'backend-services-health',
            services_health_url,
            expected_status=200,
            description="Backend Services Health Check"
        )

    def _test_api_endpoints(self):
        """Test API endpoints."""
        print_info("Testing API endpoints...")

        api_gateway_url = self._get_service_url('api-gateway')

        if not api_gateway_url:
            print_warning("API Gateway URL not found, skipping API tests")
            return

        # Test Swagger documentation
        swagger_url = f"{api_gateway_url}/api/docs"
        self._test_http_endpoint(
            'swagger-docs',
            swagger_url,
            expected_status=200,
            description="Swagger Documentation"
        )

    def _get_service_url(self, service_name: str) -> Optional[str]:
        """Get service URL."""
        returncode, stdout, stderr = run_az_command([
            'containerapp', 'show',
            '--name', service_name,
            '--resource-group', self.resource_group,
            '--query', 'properties.configuration.ingress.fqdn',
            '--output', 'tsv'
        ], check=False, logger=self.logger)

        if returncode == 0 and stdout.strip():
            return f"https://{stdout.strip()}"

        return None

    def _test_http_endpoint(
        self,
        test_name: str,
        url: str,
        expected_status: int = 200,
        description: str = None
    ):
        """Test an HTTP endpoint."""
        if description:
            print_info(f"Testing: {description}")

        result = {
            'url': url,
            'expected_status': expected_status
        }

        try:
            if HAS_REQUESTS:
                response = requests.get(url, timeout=10)
                status_code = response.status_code
                result['status_code'] = status_code
                result['response_time'] = response.elapsed.total_seconds()

                if status_code == expected_status:
                    print_success(f"  ✓ {url} returned {status_code}")
                    result['status'] = 'passed'
                    self.results['summary']['passed'] += 1
                else:
                    print_error(f"  ✗ {url} returned {status_code} (expected {expected_status})")
                    result['status'] = 'failed'
                    result['response_body'] = response.text[:500]  # First 500 chars
                    self.results['summary']['failed'] += 1
            else:
                # Fallback to curl
                cmd = ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', '10', url]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                status_code = int(proc.stdout.strip()) if proc.stdout.strip() else 0
                result['status_code'] = status_code

                if status_code == expected_status:
                    print_success(f"  ✓ {url} returned {status_code}")
                    result['status'] = 'passed'
                    self.results['summary']['passed'] += 1
                else:
                    print_error(f"  ✗ {url} returned {status_code} (expected {expected_status})")
                    result['status'] = 'failed'
                    self.results['summary']['failed'] += 1

        except Exception as e:
            print_error(f"  ✗ Failed to test {url}: {str(e)}")
            result['status'] = 'failed'
            result['error'] = str(e)
            self.results['summary']['failed'] += 1

        self.results['services'][test_name] = result
        self.results['summary']['total_tests'] += 1

    def _print_summary(self):
        """Print test summary."""
        print_header("Test Summary")

        total = self.results['summary']['total_tests']
        passed = self.results['summary']['passed']
        failed = self.results['summary']['failed']
        warnings = self.results['summary']['warnings']

        print_info(f"Total tests: {total}")
        print_success(f"Passed: {passed}")

        if warnings > 0:
            print_warning(f"Warnings: {warnings}")

        if failed > 0:
            print_error(f"Failed: {failed}")
        else:
            print_success("All tests passed! 🎉")

        # Print failed services
        if failed > 0:
            print_header("Failed Tests")
            for service_name, service_result in self.results['services'].items():
                if service_result.get('status') == 'failed':
                    print_error(f"  - {service_name}")
                    if 'error' in service_result:
                        print_info(f"    Error: {service_result['error']}")

            for infra_name, infra_result in self.results['infrastructure'].items():
                if infra_result.get('status') == 'failed':
                    print_error(f"  - {infra_name}")
                    if 'error' in infra_result:
                        print_info(f"    Error: {infra_result['error']}")

    def save_report(self, report_path: str):
        """Save test report to file."""
        try:
            with open(report_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            print_success(f"Test report saved to: {report_path}")
        except Exception as e:
            print_error(f"Failed to save report: {str(e)}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Test DraftGenie Azure Deployment',
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
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--report',
        type=str,
        default='azure-test-report.json',
        help='Path to save test report (default: azure-test-report.json)'
    )

    parser.add_argument(
        '--skip-logs',
        action='store_true',
        help='Skip fetching logs for failed services'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(
        verbose=args.verbose,
        log_file='azure-testing.log'
    )

    # Load configuration
    config_path = args.config

    if not os.path.exists(config_path):
        print_error(f"Configuration file not found: {config_path}")
        print_info("Please create a configuration file or specify a different path with --config")
        sys.exit(1)

    print_info(f"Loading configuration from {config_path}")
    config = load_config(config_path)

    # Create tester
    tester = AzureServiceTester(
        config=config,
        logger=logger,
        verbose=args.verbose
    )

    # Run tests
    success = tester.run_all_tests()

    # Save report
    if args.report:
        tester.save_report(args.report)

    # Exit with appropriate code
    if success:
        print_success("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print_error("\n❌ Some tests failed")
        print_info("\nNext steps:")
        print_info("1. Review the test report for details")
        print_info("2. Check service logs: az containerapp logs show --name <service-name> --resource-group draftgenie-rg")
        print_info("3. Verify environment variables are configured correctly")
        print_info("4. Run fix script if needed: ./scripts/azure/fix-environment-variables.sh")
        sys.exit(1)


if __name__ == '__main__':
    main()


