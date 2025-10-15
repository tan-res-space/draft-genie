/**
 * Centralized Port Configuration Reader
 * 
 * This module reads port numbers from the centralized config/ports.json file.
 * It provides a single source of truth for port assignments across all services.
 */

import * as fs from 'fs';
import * as path from 'path';

interface PortConfig {
  services: {
    [key: string]: {
      port: number;
      description: string;
      protocol: string;
      healthEndpoint: string;
    };
  };
  infrastructure: {
    [key: string]: {
      port: number;
      description: string;
      protocol: string;
      grpcPort?: number;
      managementPort?: number;
    };
  };
}

let cachedConfig: PortConfig | null = null;

/**
 * Load the ports configuration from config/ports.json
 */
function loadPortsConfig(): PortConfig {
  if (cachedConfig) {
    return cachedConfig;
  }

  try {
    // Find the project root by looking for config/ports.json
    let currentDir = __dirname;
    let configPath: string | null = null;
    
    // Search up to 5 levels up
    for (let i = 0; i < 5; i++) {
      const testPath = path.join(currentDir, 'config', 'ports.json');
      if (fs.existsSync(testPath)) {
        configPath = testPath;
        break;
      }
      currentDir = path.dirname(currentDir);
    }

    if (!configPath) {
      throw new Error('config/ports.json not found');
    }

    const configContent = fs.readFileSync(configPath, 'utf-8');
    cachedConfig = JSON.parse(configContent);
    return cachedConfig!;
  } catch (error) {
    console.error('Failed to load ports configuration:', error);
    throw error;
  }
}

/**
 * Get the port number for a service
 * 
 * @param serviceName - Name of the service (e.g., 'api-gateway', 'speaker-service')
 * @param defaultPort - Default port to use if config is not available
 * @returns Port number
 */
export function getServicePort(serviceName: string, defaultPort: number): number {
  // First check environment variable
  const envPort = process.env['PORT'];
  if (envPort) {
    return parseInt(envPort, 10);
  }

  // Then check config file
  try {
    const config = loadPortsConfig();
    const serviceConfig = config.services[serviceName];
    
    if (serviceConfig && serviceConfig.port) {
      return serviceConfig.port;
    }
  } catch (error) {
    console.warn(`Failed to read port from config for ${serviceName}, using default: ${defaultPort}`);
  }

  return defaultPort;
}

/**
 * Get the port number for an infrastructure service
 * 
 * @param serviceName - Name of the infrastructure service (e.g., 'postgres', 'mongodb')
 * @param defaultPort - Default port to use if config is not available
 * @returns Port number
 */
export function getInfrastructurePort(serviceName: string, defaultPort: number): number {
  try {
    const config = loadPortsConfig();
    const infraConfig = config.infrastructure[serviceName];
    
    if (infraConfig && infraConfig.port) {
      return infraConfig.port;
    }
  } catch (error) {
    console.warn(`Failed to read port from config for ${serviceName}, using default: ${defaultPort}`);
  }

  return defaultPort;
}

/**
 * Get all service ports
 * 
 * @returns Object with service names as keys and port numbers as values
 */
export function getAllServicePorts(): Record<string, number> {
  try {
    const config = loadPortsConfig();
    const ports: Record<string, number> = {};
    
    for (const [serviceName, serviceConfig] of Object.entries(config.services)) {
      ports[serviceName] = serviceConfig.port;
    }
    
    return ports;
  } catch (error) {
    console.error('Failed to get all service ports:', error);
    return {};
  }
}

