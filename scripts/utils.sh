#!/bin/bash

# DraftGenie Utility Functions
# Shared functions for start.sh and stop.sh scripts

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="${PROJECT_ROOT}/.pids"
CONFIG_FILE="${PROJECT_ROOT}/config/ports.json"

# Ensure PID directory exists
mkdir -p "${PID_DIR}"

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print section header
print_header() {
    local message=$1
    echo ""
    print_message "${CYAN}" "========================================="
    print_message "${CYAN}" "$message"
    print_message "${CYAN}" "========================================="
}

# Print success message
print_success() {
    print_message "${GREEN}" "✅ $1"
}

# Print error message
print_error() {
    print_message "${RED}" "❌ $1"
}

# Print warning message
print_warning() {
    print_message "${YELLOW}" "⚠️  $1"
}

# Print info message
print_info() {
    print_message "${BLUE}" "ℹ️  $1"
}

# Check if jq is installed
check_jq() {
    if ! command -v jq &> /dev/null; then
        print_error "jq is not installed. Please install it first:"
        echo "  macOS: brew install jq"
        echo "  Linux: sudo apt-get install jq"
        exit 1
    fi
}

# Read port from config file
get_port() {
    local service=$1
    check_jq
    
    if [ ! -f "${CONFIG_FILE}" ]; then
        print_error "Config file not found: ${CONFIG_FILE}"
        exit 1
    fi
    
    local port=$(jq -r ".services.\"${service}\".port // .infrastructure.\"${service}\".port // empty" "${CONFIG_FILE}")
    
    if [ -z "$port" ]; then
        print_error "Port not found for service: ${service}"
        exit 1
    fi
    
    echo "$port"
}

# Check if a port is in use
is_port_in_use() {
    local port=$1
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Get process using a port
get_process_on_port() {
    local port=$1
    lsof -Pi :${port} -sTCP:LISTEN -t 2>/dev/null
}

# Check if a service is running by PID file
is_service_running() {
    local service=$1
    local pid_file="${PID_DIR}/${service}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Service is running
        else
            # PID file exists but process is dead, clean up
            rm -f "$pid_file"
            return 1  # Service is not running
        fi
    fi
    return 1  # Service is not running
}

# Save PID for a service
save_pid() {
    local service=$1
    local pid=$2
    echo "$pid" > "${PID_DIR}/${service}.pid"
}

# Get PID for a service
get_pid() {
    local service=$1
    local pid_file="${PID_DIR}/${service}.pid"
    
    if [ -f "$pid_file" ]; then
        cat "$pid_file"
    fi
}

# Remove PID file for a service
remove_pid() {
    local service=$1
    rm -f "${PID_DIR}/${service}.pid"
}

# Wait for a service to be healthy
wait_for_health() {
    local service=$1
    local port=$2
    local endpoint=${3:-"/health"}
    local max_attempts=${4:-30}
    local attempt=0
    
    print_info "Waiting for ${service} to be healthy..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
            print_success "${service} is healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 1
    done
    
    print_error "${service} failed to become healthy after ${max_attempts} seconds"
    return 1
}

# Check Docker service health
check_docker_service() {
    local service=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' "draft-genie-${service}" 2>/dev/null)
    
    if [ "$status" = "healthy" ]; then
        return 0
    else
        return 1
    fi
}

# Wait for Docker service to be healthy
wait_for_docker_service() {
    local service=$1
    local max_attempts=${2:-60}
    local attempt=0
    
    print_info "Waiting for Docker service ${service} to be healthy..."
    
    while [ $attempt -lt $max_attempts ]; do
        if check_docker_service "$service"; then
            print_success "Docker service ${service} is healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 1
    done
    
    print_error "Docker service ${service} failed to become healthy after ${max_attempts} seconds"
    return 1
}

# Kill process gracefully
kill_process() {
    local pid=$1
    local service=$2
    local timeout=${3:-10}
    
    if [ -z "$pid" ]; then
        return 0
    fi
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        return 0
    fi
    
    print_info "Stopping ${service} (PID: ${pid})..."
    
    # Try graceful shutdown first
    kill -TERM "$pid" 2>/dev/null
    
    # Wait for process to exit
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt $timeout ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "Force killing ${service} (PID: ${pid})..."
        kill -KILL "$pid" 2>/dev/null
        sleep 1
    fi
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        print_success "${service} stopped"
        return 0
    else
        print_error "Failed to stop ${service}"
        return 1
    fi
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 20+."
        exit 1
    fi
}

# Check if npm is installed
check_npm() {
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm."
        exit 1
    fi
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+."
        exit 1
    fi
}

# Check if Poetry is installed
check_poetry() {
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is not installed. Please install Poetry."
        echo "  Install: curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
}

# Display service status
show_service_status() {
    local service=$1
    local port=$2
    
    if is_service_running "$service"; then
        local pid=$(get_pid "$service")
        print_success "${service} is running (PID: ${pid}, Port: ${port})"
    else
        print_warning "${service} is not running"
    fi
}

# Export functions for use in other scripts
export -f print_message
export -f print_header
export -f print_success
export -f print_error
export -f print_warning
export -f print_info
export -f check_jq
export -f get_port
export -f is_port_in_use
export -f get_process_on_port
export -f is_service_running
export -f save_pid
export -f get_pid
export -f remove_pid
export -f wait_for_health
export -f check_docker_service
export -f wait_for_docker_service
export -f kill_process
export -f check_docker
export -f check_node
export -f check_npm
export -f check_python
export -f check_poetry
export -f show_service_status

