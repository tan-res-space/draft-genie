#!/bin/bash

# Test draft-service and rag-service after PostgreSQL migration
# This script verifies that the services are working correctly with PostgreSQL

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="rg-dg-backend-v01"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing PostgreSQL Migration${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to test a service
test_service() {
    local service_name=$1
    local test_passed=true
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Testing ${service_name}${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Get service URL
    echo -e "${YELLOW}Fetching service URL...${NC}"
    SERVICE_URL=$(az containerapp show \
        --name ${service_name} \
        --resource-group ${RESOURCE_GROUP} \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv 2>/dev/null)
    
    if [ -z "$SERVICE_URL" ]; then
        echo -e "${RED}✗ Could not fetch service URL${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Service URL: https://${SERVICE_URL}${NC}"
    
    # Test 1: Basic health check
    echo ""
    echo -e "${YELLOW}Test 1: Basic health check (/health)${NC}"
    RESPONSE=$(curl -s -w "\n%{http_code}" "https://${SERVICE_URL}/health" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Health check passed (HTTP $HTTP_CODE)${NC}"
        echo -e "${BLUE}Response: ${BODY}${NC}"
    else
        echo -e "${RED}✗ Health check failed (HTTP $HTTP_CODE)${NC}"
        test_passed=false
    fi
    
    # Test 2: Readiness check (includes database connectivity)
    echo ""
    echo -e "${YELLOW}Test 2: Readiness check (/health/ready)${NC}"
    RESPONSE=$(curl -s -w "\n%{http_code}" "https://${SERVICE_URL}/health/ready" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Readiness check passed (HTTP $HTTP_CODE)${NC}"
        echo -e "${BLUE}Response: ${BODY}${NC}"
        
        # Check if PostgreSQL is healthy
        if echo "$BODY" | grep -q '"postgresql".*true'; then
            echo -e "${GREEN}✓ PostgreSQL connection confirmed${NC}"
        elif echo "$BODY" | grep -q '"postgresql".*false'; then
            echo -e "${RED}✗ PostgreSQL connection failed${NC}"
            test_passed=false
        fi
    else
        echo -e "${RED}✗ Readiness check failed (HTTP $HTTP_CODE)${NC}"
        echo -e "${RED}Response: ${BODY}${NC}"
        test_passed=false
    fi
    
    # Test 3: Liveness check
    echo ""
    echo -e "${YELLOW}Test 3: Liveness check (/health/live)${NC}"
    RESPONSE=$(curl -s -w "\n%{http_code}" "https://${SERVICE_URL}/health/live" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Liveness check passed (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${RED}✗ Liveness check failed (HTTP $HTTP_CODE)${NC}"
        test_passed=false
    fi
    
    # Test 4: Check service logs for errors
    echo ""
    echo -e "${YELLOW}Test 4: Checking recent logs for errors${NC}"
    LOGS=$(az containerapp logs show \
        --name ${service_name} \
        --resource-group ${RESOURCE_GROUP} \
        --tail 50 \
        --output table 2>/dev/null || echo "")
    
    if echo "$LOGS" | grep -qi "error\|exception\|failed"; then
        echo -e "${YELLOW}⚠ Found errors in logs (check manually)${NC}"
        echo "$LOGS" | grep -i "error\|exception\|failed" | head -n 5
    else
        echo -e "${GREEN}✓ No obvious errors in recent logs${NC}"
    fi
    
    # Test 5: Check running status
    echo ""
    echo -e "${YELLOW}Test 5: Checking running status${NC}"
    STATUS=$(az containerapp show \
        --name ${service_name} \
        --resource-group ${RESOURCE_GROUP} \
        --query "properties.runningStatus" \
        --output tsv 2>/dev/null)
    
    if [ "$STATUS" = "Running" ]; then
        echo -e "${GREEN}✓ Service is running${NC}"
    else
        echo -e "${RED}✗ Service status: ${STATUS}${NC}"
        test_passed=false
    fi
    
    # Summary
    echo ""
    if [ "$test_passed" = true ]; then
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✓ All tests passed for ${service_name}${NC}"
        echo -e "${GREEN}========================================${NC}"
        return 0
    else
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}✗ Some tests failed for ${service_name}${NC}"
        echo -e "${RED}========================================${NC}"
        return 1
    fi
}

# Test draft-service
DRAFT_RESULT=0
test_service "draft-service" || DRAFT_RESULT=$?

# Test rag-service
RAG_RESULT=0
test_service "rag-service" || RAG_RESULT=$?

# Overall summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Overall Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $DRAFT_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ draft-service: PASSED${NC}"
else
    echo -e "${RED}✗ draft-service: FAILED${NC}"
fi

if [ $RAG_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ rag-service: PASSED${NC}"
else
    echo -e "${RED}✗ rag-service: FAILED${NC}"
fi

echo ""

if [ $DRAFT_RESULT -eq 0 ] && [ $RAG_RESULT -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🎉 PostgreSQL Migration Successful!${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}⚠ Some services failed tests${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting steps:${NC}"
    echo "1. Check service logs:"
    echo "   az containerapp logs show --name draft-service --resource-group ${RESOURCE_GROUP} --follow"
    echo "   az containerapp logs show --name rag-service --resource-group ${RESOURCE_GROUP} --follow"
    echo ""
    echo "2. Verify DATABASE_URL environment variable is set correctly"
    echo ""
    echo "3. Check PostgreSQL connectivity from container apps"
    echo ""
    echo "4. Verify database migrations were run successfully"
    echo ""
    exit 1
fi

