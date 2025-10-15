#!/bin/bash

# DraftGenie - Start All Services
# This script starts all DraftGenie services in the correct order

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Source utility functions
source "${SCRIPT_DIR}/utils.sh"

# Change to project root
cd "${PROJECT_ROOT}"

# Main function
main() {
    print_header "🚀 Starting DraftGenie Services"
    
    # Check prerequisites
    check_prerequisites
    
    # Check if services are already running
    check_running_services
    
    # Start Docker infrastructure
    start_docker_infrastructure
    
    # Wait for infrastructure to be ready
    wait_for_infrastructure
    
    # Start microservices
    start_microservices
    
    # Display status
    display_status
    
    print_header "✅ All Services Started Successfully"
    print_info "API Gateway: http://localhost:$(get_port api-gateway)"
    print_info "API Documentation: http://localhost:$(get_port api-gateway)/api/docs"
    print_info ""
    print_info "To stop all services, run: ./scripts/stop.sh"
    print_info "To view logs, run: npm run docker:logs"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    check_jq
    check_docker
    check_node
    check_npm
    check_python
    check_poetry
    
    print_success "All prerequisites satisfied"
}

# Check if services are already running
check_running_services() {
    print_header "Checking Running Services"
    
    local services=("api-gateway" "speaker-service" "draft-service" "rag-service" "evaluation-service")
    local running_services=()
    
    for service in "${services[@]}"; do
        if is_service_running "$service"; then
            running_services+=("$service")
        fi
    done
    
    if [ ${#running_services[@]} -gt 0 ]; then
        print_warning "The following services are already running:"
        for service in "${running_services[@]}"; do
            local pid=$(get_pid "$service")
            local port=$(get_port "$service")
            echo "  - ${service} (PID: ${pid}, Port: ${port})"
        done
        echo ""
        read -p "Do you want to restart them? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Stopping running services..."
            "${SCRIPT_DIR}/stop.sh"
            sleep 2
        else
            print_info "Keeping existing services running. Starting only stopped services..."
        fi
    else
        print_success "No services currently running"
    fi
}

# Start Docker infrastructure
start_docker_infrastructure() {
    print_header "Starting Docker Infrastructure"
    
    # Check if .env file exists
    if [ ! -f "${PROJECT_ROOT}/docker/.env" ]; then
        print_warning "docker/.env not found. Creating from docker/.env.example..."
        cp "${PROJECT_ROOT}/docker/.env.example" "${PROJECT_ROOT}/docker/.env"
        print_info "Please edit docker/.env and add your GEMINI_API_KEY"
        print_info "Then run this script again."
        exit 1
    fi
    
    # Start Docker Compose services
    print_info "Starting Docker Compose services..."
    cd "${PROJECT_ROOT}"
    npm run docker:up
    
    print_success "Docker infrastructure started"
}

# Wait for infrastructure to be ready
wait_for_infrastructure() {
    print_header "Waiting for Infrastructure Services"
    
    local services=("postgres" "mongodb" "qdrant" "redis" "rabbitmq")
    
    for service in "${services[@]}"; do
        wait_for_docker_service "$service" 60
    done
    
    print_success "All infrastructure services are healthy"
}

# Start microservices
start_microservices() {
    print_header "Starting Microservices"
    
    # Start Speaker Service (TypeScript/NestJS)
    start_speaker_service
    
    # Start Draft Service (Python/FastAPI)
    start_draft_service
    
    # Start RAG Service (Python/FastAPI)
    start_rag_service
    
    # Start Evaluation Service (Python/FastAPI)
    start_evaluation_service
    
    # Start API Gateway (TypeScript/NestJS)
    start_api_gateway
    
    print_success "All microservices started"
}

# Start Speaker Service
start_speaker_service() {
    local service="speaker-service"
    
    if is_service_running "$service"; then
        print_info "${service} is already running"
        return 0
    fi
    
    local port=$(get_port "$service")
    
    print_info "Starting ${service} on port ${port}..."
    
    cd "${PROJECT_ROOT}"
    npm run dev:speaker > "${PROJECT_ROOT}/.logs/${service}.log" 2>&1 &
    local pid=$!
    save_pid "$service" "$pid"
    
    wait_for_health "$service" "$port" "/health" 30
}

# Start Draft Service
start_draft_service() {
    local service="draft-service"
    
    if is_service_running "$service"; then
        print_info "${service} is already running"
        return 0
    fi
    
    local port=$(get_port "$service")
    
    print_info "Starting ${service} on port ${port}..."
    
    cd "${PROJECT_ROOT}/services/draft-service"
    PORT=$port poetry run uvicorn app.main:app --host 0.0.0.0 --port $port --reload > "${PROJECT_ROOT}/.logs/${service}.log" 2>&1 &
    local pid=$!
    save_pid "$service" "$pid"
    
    cd "${PROJECT_ROOT}"
    wait_for_health "$service" "$port" "/health" 30
}

# Start RAG Service
start_rag_service() {
    local service="rag-service"
    
    if is_service_running "$service"; then
        print_info "${service} is already running"
        return 0
    fi
    
    local port=$(get_port "$service")
    
    print_info "Starting ${service} on port ${port}..."
    
    cd "${PROJECT_ROOT}/services/rag-service"
    PORT=$port poetry run uvicorn app.main:app --host 0.0.0.0 --port $port --reload > "${PROJECT_ROOT}/.logs/${service}.log" 2>&1 &
    local pid=$!
    save_pid "$service" "$pid"
    
    cd "${PROJECT_ROOT}"
    wait_for_health "$service" "$port" "/health" 30
}

# Start Evaluation Service
start_evaluation_service() {
    local service="evaluation-service"
    
    if is_service_running "$service"; then
        print_info "${service} is already running"
        return 0
    fi
    
    local port=$(get_port "$service")
    
    print_info "Starting ${service} on port ${port}..."
    
    cd "${PROJECT_ROOT}/services/evaluation-service"
    PORT=$port poetry run uvicorn app.main:app --host 0.0.0.0 --port $port --reload > "${PROJECT_ROOT}/.logs/${service}.log" 2>&1 &
    local pid=$!
    save_pid "$service" "$pid"
    
    cd "${PROJECT_ROOT}"
    wait_for_health "$service" "$port" "/health" 30
}

# Start API Gateway
start_api_gateway() {
    local service="api-gateway"
    
    if is_service_running "$service"; then
        print_info "${service} is already running"
        return 0
    fi
    
    local port=$(get_port "$service")
    
    print_info "Starting ${service} on port ${port}..."
    
    cd "${PROJECT_ROOT}"
    npm run dev:gateway > "${PROJECT_ROOT}/.logs/${service}.log" 2>&1 &
    local pid=$!
    save_pid "$service" "$pid"
    
    wait_for_health "$service" "$port" "/health" 30
}

# Display status of all services
display_status() {
    print_header "Service Status"
    
    local services=("api-gateway" "speaker-service" "draft-service" "rag-service" "evaluation-service")
    
    for service in "${services[@]}"; do
        local port=$(get_port "$service")
        show_service_status "$service" "$port"
    done
}

# Create logs directory
mkdir -p "${PROJECT_ROOT}/.logs"

# Run main function
main

