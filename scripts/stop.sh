#!/bin/bash

# DraftGenie - Stop All Services
# This script stops all DraftGenie services gracefully

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
    print_header "🛑 Stopping DraftGenie Services"
    
    # Check if any services are running
    check_services
    
    # Stop microservices
    stop_microservices
    
    # Optionally stop Docker infrastructure
    stop_docker_infrastructure
    
    # Clean up
    cleanup
    
    print_header "✅ All Services Stopped Successfully"
}

# Check if any services are running
check_services() {
    print_header "Checking Running Services"
    
    local services=("api-gateway" "speaker-service" "draft-service" "rag-service" "evaluation-service")
    local running_count=0
    
    for service in "${services[@]}"; do
        if is_service_running "$service"; then
            running_count=$((running_count + 1))
            local pid=$(get_pid "$service")
            local port=$(get_port "$service")
            print_info "${service} is running (PID: ${pid}, Port: ${port})"
        fi
    done
    
    if [ $running_count -eq 0 ]; then
        print_warning "No microservices are currently running"
    else
        print_info "Found ${running_count} running service(s)"
    fi
}

# Stop microservices
stop_microservices() {
    print_header "Stopping Microservices"
    
    local services=("api-gateway" "evaluation-service" "rag-service" "draft-service" "speaker-service")
    local stopped_count=0
    
    for service in "${services[@]}"; do
        if is_service_running "$service"; then
            local pid=$(get_pid "$service")
            if kill_process "$pid" "$service" 10; then
                remove_pid "$service"
                stopped_count=$((stopped_count + 1))
            fi
        else
            print_info "${service} is not running"
        fi
    done
    
    if [ $stopped_count -gt 0 ]; then
        print_success "Stopped ${stopped_count} service(s)"
    fi
}

# Stop Docker infrastructure
stop_docker_infrastructure() {
    print_header "Docker Infrastructure"
    
    # Check if Docker services are running
    if ! docker ps --format '{{.Names}}' | grep -q "draft-genie-"; then
        print_info "No Docker services are running"
        return 0
    fi
    
    echo ""
    read -p "Do you want to stop Docker infrastructure (postgres, mongodb, etc.)? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping Docker infrastructure..."
        cd "${PROJECT_ROOT}"
        npm run docker:down
        print_success "Docker infrastructure stopped"
    else
        print_info "Keeping Docker infrastructure running"
    fi
}

# Clean up temporary files
cleanup() {
    print_header "Cleaning Up"
    
    # Clean up any orphaned PID files
    local pid_dir="${PROJECT_ROOT}/.pids"
    if [ -d "$pid_dir" ]; then
        for pid_file in "$pid_dir"/*.pid; do
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file")
                if ! ps -p "$pid" > /dev/null 2>&1; then
                    print_info "Removing orphaned PID file: $(basename "$pid_file")"
                    rm -f "$pid_file"
                fi
            fi
        done
    fi
    
    print_success "Cleanup complete"
}

# Run main function
main

