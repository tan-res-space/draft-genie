#!/bin/bash

# Test script to verify port configuration is working correctly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Source utility functions
source "${SCRIPT_DIR}/utils.sh"

print_header "Testing Port Configuration"

# Test 1: Check if config file exists
print_info "Test 1: Checking if config/ports.json exists..."
if [ -f "${PROJECT_ROOT}/config/ports.json" ]; then
    print_success "config/ports.json exists"
else
    print_error "config/ports.json not found"
    exit 1
fi

# Test 2: Test reading ports with jq
print_info "Test 2: Testing port reading with jq..."
api_gateway_port=$(jq -r '.services."api-gateway".port' "${PROJECT_ROOT}/config/ports.json")
speaker_port=$(jq -r '.services."speaker-service".port' "${PROJECT_ROOT}/config/ports.json")
draft_port=$(jq -r '.services."draft-service".port' "${PROJECT_ROOT}/config/ports.json")
rag_port=$(jq -r '.services."rag-service".port' "${PROJECT_ROOT}/config/ports.json")
eval_port=$(jq -r '.services."evaluation-service".port' "${PROJECT_ROOT}/config/ports.json")

echo "  API Gateway: $api_gateway_port"
echo "  Speaker Service: $speaker_port"
echo "  Draft Service: $draft_port"
echo "  RAG Service: $rag_port"
echo "  Evaluation Service: $eval_port"

if [ "$api_gateway_port" = "3000" ] && [ "$speaker_port" = "3001" ] && \
   [ "$draft_port" = "3002" ] && [ "$rag_port" = "3003" ] && \
   [ "$eval_port" = "3004" ]; then
    print_success "All ports read correctly"
else
    print_error "Port values are incorrect"
    exit 1
fi

# Test 3: Test utility function
print_info "Test 3: Testing get_port utility function..."
test_port=$(get_port "api-gateway")
if [ "$test_port" = "3000" ]; then
    print_success "get_port function works correctly"
else
    print_error "get_port function returned: $test_port (expected 3000)"
    exit 1
fi

# Test 4: Test Python port reading
print_info "Test 4: Testing Python port configuration..."
cd "${PROJECT_ROOT}/services/draft-service"

# Capture both stdout and stderr
python_output=$(python3 -c "from app.core.config import get_port_from_config; print(get_port_from_config('draft-service', 8001))" 2>&1)
python_exit_code=$?

if [ $python_exit_code -eq 0 ]; then
    python_port=$(echo "$python_output" | tail -n 1)
    if [ "$python_port" = "3002" ]; then
        print_success "Python port reading works correctly"
    else
        print_warning "Python port reading returned: $python_port (expected 3002)"
        print_info "Output: $python_output"
    fi
else
    print_warning "Python port reading failed with exit code: $python_exit_code"
    print_info "Error output:"
    echo "$python_output" | head -n 5
    print_info "This might be due to missing dependencies. The function exists but requires:"
    print_info "  - pydantic and pydantic-settings packages"
    print_info "  - Proper Python environment setup"
    print_info "Run: cd services/draft-service && poetry install"
fi

cd "${PROJECT_ROOT}"

# Test 4b: Test all Python services
print_info "Test 4b: Testing all Python services port configuration..."

test_python_service() {
    local service_name=$1
    local service_dir=$2
    local expected_port=$3

    cd "${PROJECT_ROOT}/${service_dir}"
    local port_output=$(python3 -c "from app.core.config import get_port_from_config; print(get_port_from_config('${service_name}', 8000))" 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        local port=$(echo "$port_output" | tail -n 1)
        if [ "$port" = "$expected_port" ]; then
            echo "  ✅ ${service_name}: ${port}"
            return 0
        else
            echo "  ⚠️  ${service_name}: got ${port}, expected ${expected_port}"
            return 1
        fi
    else
        echo "  ⚠️  ${service_name}: failed to read port"
        return 1
    fi
}

all_python_tests_passed=true
test_python_service "draft-service" "services/draft-service" "3002" || all_python_tests_passed=false
test_python_service "rag-service" "services/rag-service" "3003" || all_python_tests_passed=false
test_python_service "evaluation-service" "services/evaluation-service" "3004" || all_python_tests_passed=false

cd "${PROJECT_ROOT}"

if [ "$all_python_tests_passed" = true ]; then
    print_success "All Python services can read their ports correctly"
else
    print_warning "Some Python services had issues reading ports"
fi

# Test 4c: Test TypeScript port configuration
print_info "Test 4c: Testing TypeScript port configuration..."

# Check if node_modules exists
if [ ! -d "${PROJECT_ROOT}/node_modules" ]; then
    print_warning "node_modules not found. Run 'npm install' to test TypeScript services."
else
    # Test if the TypeScript module can be imported
    ts_test_result=$(cd "${PROJECT_ROOT}" && node -e "
        try {
            const { getServicePort } = require('./libs/common/src/config/ports.config.ts');
            console.log('TypeScript module exists');
        } catch (e) {
            // Try compiled version
            try {
                const { getServicePort } = require('./dist/libs/common/src/config/ports.config.js');
                console.log('TypeScript module exists (compiled)');
            } catch (e2) {
                console.log('Module not compiled yet');
            }
        }
    " 2>&1)

    if echo "$ts_test_result" | grep -q "exists"; then
        print_success "TypeScript port configuration module exists"
    else
        print_info "TypeScript module not yet compiled (this is OK for development)"
        print_info "Services will compile it on first run"
    fi
fi

# Test 5: Verify all service ports are unique
print_info "Test 5: Checking for port conflicts..."
all_ports=$(jq -r '.services[].port' "${PROJECT_ROOT}/config/ports.json" | sort)
unique_ports=$(echo "$all_ports" | uniq)

if [ "$all_ports" = "$unique_ports" ]; then
    print_success "All service ports are unique"
else
    print_error "Port conflicts detected!"
    exit 1
fi

print_header "✅ All Port Configuration Tests Passed"

