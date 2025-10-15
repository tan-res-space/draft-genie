# Service Management Guide

This guide explains how to start, stop, and manage all DraftGenie services using the centralized management scripts.

## Overview

DraftGenie provides automated scripts for managing all services with proper dependency handling, health checks, and centralized port configuration.

## Quick Start

### Start All Services

```bash
./scripts/start.sh
```

This will:
1. ✅ Check prerequisites (Docker, Node.js, Python, Poetry, jq)
2. ✅ Check if services are already running
3. ✅ Start Docker infrastructure (PostgreSQL, MongoDB, Qdrant, Redis, RabbitMQ)
4. ✅ Wait for infrastructure to be healthy
5. ✅ Start all microservices in the correct order
6. ✅ Verify each service is healthy before proceeding
7. ✅ Display status of all services

### Stop All Services

```bash
./scripts/stop.sh
```

This will:
1. ✅ Stop all running microservices gracefully
2. ✅ Optionally stop Docker infrastructure
3. ✅ Clean up PID files
4. ✅ Display final status

## Centralized Port Configuration

All service ports are managed in a single configuration file: `config/ports.json`

### Benefits

- **Single Source of Truth**: All port assignments in one place
- **Environment Parity**: Same ports in development, testing, and production
- **Easy Management**: Change ports in one place, restart service
- **No Conflicts**: Centralized view prevents port conflicts

### Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 3000 | Main entry point for all client requests |
| Speaker Service | 3001 | Speaker data and profiles management |
| Draft Service | 3002 | Draft ingestion and processing |
| RAG Service | 3003 | Retrieval-Augmented Generation with Gemini |
| Evaluation Service | 3004 | Draft quality evaluation and metrics |

### Changing Ports

To change a service port:

1. Edit `config/ports.json`:
   ```json
   {
     "services": {
       "api-gateway": {
         "port": 3000,  // Change this
         "description": "API Gateway - Main entry point",
         "protocol": "http",
         "healthEndpoint": "/health"
       }
     }
   }
   ```

2. Restart the affected service:
   ```bash
   ./scripts/stop.sh
   ./scripts/start.sh
   ```

## Service Logs

Service logs are saved to the `.logs/` directory:

- `.logs/api-gateway.log`
- `.logs/speaker-service.log`
- `.logs/draft-service.log`
- `.logs/rag-service.log`
- `.logs/evaluation-service.log`

View logs in real-time:
```bash
tail -f .logs/api-gateway.log
```

## Process Management

The scripts use PID files to track running services:

- PID files are stored in `.pids/` directory
- Each service has its own PID file (e.g., `.pids/api-gateway.pid`)
- PID files are automatically cleaned up on service stop

## Health Checks

Each service is verified to be healthy before the start script proceeds:

- **Health Endpoint**: `/health` for all services
- **Timeout**: 30 seconds per service
- **Retry Interval**: 1 second

If a service fails to become healthy, the script will report an error.

## Troubleshooting

### Services Won't Start

1. Check if ports are already in use:
   ```bash
   lsof -i :3000  # Check API Gateway port
   ```

2. Check Docker services:
   ```bash
   docker ps
   npm run docker:logs
   ```

3. Check service logs:
   ```bash
   cat .logs/api-gateway.log
   ```

### Port Conflicts

If you get port conflicts:

1. Edit `config/ports.json` to use different ports
2. Restart the services

### Services Already Running

If services are already running, the start script will:
1. Detect running services
2. Ask if you want to restart them
3. Stop and restart if confirmed
4. Skip and continue if declined

### Docker Not Running

If Docker is not running:
```bash
# macOS
open -a Docker

# Or start Docker Desktop manually
```

### Missing Dependencies

If you're missing dependencies:

```bash
# Install jq (required for reading config)
# macOS
brew install jq

# Linux
sudo apt-get install jq

# Install Node.js dependencies
npm install

# Install Python dependencies
cd services/draft-service && poetry install
cd ../rag-service && poetry install
cd ../evaluation-service && poetry install
```

## Advanced Usage

### Start Individual Services

```bash
# Start only specific services
npm run dev:speaker
npm run dev:draft
npm run dev:rag
npm run dev:evaluation
npm run dev:gateway
```

### Check Service Status

```bash
# Check if a service is running
ps aux | grep "speaker-service"

# Check port usage
lsof -i :3001
```

### Manual Service Management

```bash
# Start Docker infrastructure only
npm run docker:up

# Stop Docker infrastructure only
npm run docker:down

# View Docker logs
npm run docker:logs
```

## Environment Variables

Services can override port configuration using environment variables:

```bash
# Override port for a specific service
PORT=4000 npm run dev:gateway
```

Priority order:
1. `PORT` environment variable (highest priority)
2. `config/ports.json` configuration
3. Default port in service code (lowest priority)

## Testing

Test the port configuration:

```bash
./scripts/test-ports.sh
```

This will verify:
- Config file exists
- Ports can be read correctly
- Utility functions work
- Python services can read ports
- No port conflicts exist

## Best Practices

1. **Always use the scripts**: Use `./scripts/start.sh` and `./scripts/stop.sh` for consistent service management
2. **Check logs**: Review `.logs/` directory when debugging issues
3. **Use centralized config**: Always update ports in `config/ports.json`, not in individual service files
4. **Verify health**: Wait for services to be healthy before making requests
5. **Clean shutdown**: Always use `./scripts/stop.sh` to gracefully stop services

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Service Management Layer                   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  start.sh    │  │   stop.sh    │  │   utils.sh   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                   ┌────────▼────────┐                       │
│                   │ config/ports.json│                      │
│                   └────────┬────────┘                       │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌───────▼────────┐
│   TypeScript   │  │     Python      │  │     Docker     │
│   Services     │  │    Services     │  │ Infrastructure │
│                │  │                 │  │                │
│ • API Gateway  │  │ • Draft Service │  │ • PostgreSQL   │
│ • Speaker Svc  │  │ • RAG Service   │  │ • MongoDB      │
│                │  │ • Eval Service  │  │ • Qdrant       │
│                │  │                 │  │ • Redis        │
│                │  │                 │  │ • RabbitMQ     │
└────────────────┘  └─────────────────┘  └────────────────┘
```

## Support

For issues or questions:
- Check the logs in `.logs/` directory
- Review [GETTING_STARTED.md](../GETTING_STARTED.md)
- Check [README.md](../README.md)
- Run `./scripts/test-ports.sh` to verify configuration

