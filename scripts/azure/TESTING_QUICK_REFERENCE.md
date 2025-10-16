# Azure Deployment Testing - Quick Reference

Quick commands and scripts for testing your Azure deployment.

---

## 🚀 Quick Test Commands

### Run Comprehensive Tests (Python)

```bash
# Run all tests with verbose output
python3 scripts/azure/test_azure_deployment.py --verbose

# Run tests and save report to custom location
python3 scripts/azure/test_azure_deployment.py --report my-test-report.json

# Run tests without verbose output
python3 scripts/azure/test_azure_deployment.py
```

### Run Basic Tests (Bash)

```bash
# Run basic service tests
./scripts/azure/test-deployed-services.sh
```

---

## 🔍 Manual Testing

### Test API Gateway

```bash
# Health check
curl https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health

# Expected response:
# {"status":"ok","info":{"gateway":{"status":"up"}},...}
```

### Test Backend Services Health

```bash
# Check all backend services through API Gateway
curl https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health/services

# Expected response:
# {"status":"ok","info":{"speaker-service":{"status":"up"},...}}
```

### Test Swagger Documentation

```bash
# Open Swagger UI in browser
open https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs

# Or test with curl
curl https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs
```

---

## 📊 Check Service Status

### List All Services

```bash
# List all container apps
az containerapp list --resource-group draftgenie-rg --output table

# List with specific columns
az containerapp list --resource-group draftgenie-rg \
  --query "[].{Name:name, Status:properties.runningStatus, URL:properties.configuration.ingress.fqdn}" \
  --output table
```

### Check Specific Service

```bash
# Get service details
az containerapp show --name api-gateway --resource-group draftgenie-rg

# Get just the status
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.runningStatus" --output tsv

# Get service URL
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.configuration.ingress.fqdn" --output tsv
```

### Check Replicas

```bash
# List replicas for a service
az containerapp replica list --name api-gateway --resource-group draftgenie-rg

# Count replicas
az containerapp replica list --name api-gateway --resource-group draftgenie-rg \
  --query "length(@)" --output tsv
```

---

## 📝 View Logs

### Recent Logs

```bash
# Last 100 lines
az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 100

# Last 50 lines
az containerapp logs show --name speaker-service --resource-group draftgenie-rg --tail 50
```

### Follow Logs (Real-time)

```bash
# Follow logs in real-time
az containerapp logs show --name api-gateway --resource-group draftgenie-rg --follow

# Press Ctrl+C to stop
```

### Logs for All Services

```bash
# Create a script to view logs from all services
for service in api-gateway speaker-service draft-service rag-service eval-service; do
  echo "=== Logs for $service ==="
  az containerapp logs show --name $service --resource-group draftgenie-rg --tail 20
  echo ""
done
```

---

## 🔧 Check Configuration

### Environment Variables

```bash
# View all environment variables for a service
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.template.containers[0].env" --output json | jq .

# Count environment variables
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "length(properties.template.containers[0].env)" --output tsv
```

### Resource Allocation

```bash
# Check CPU and memory allocation
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.template.containers[0].resources" --output json | jq .
```

### Scaling Configuration

```bash
# Check scaling settings
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.template.scale" --output json | jq .
```

---

## 🏗️ Infrastructure Tests

### PostgreSQL

```bash
# Check PostgreSQL status
az postgres flexible-server show \
  --name dg-backend-postgres \
  --resource-group draftgenie-rg \
  --query "state" --output tsv

# Expected: Ready
```

### Redis

```bash
# Check Redis status
az redis show \
  --name dg-backend-redis \
  --resource-group draftgenie-rg \
  --query "provisioningState" --output tsv

# Expected: Succeeded
```

### Key Vault

```bash
# Check Key Vault status
az keyvault show \
  --name dg-backend-kv-v01 \
  --resource-group draftgenie-rg \
  --query "properties.provisioningState" --output tsv

# Expected: Succeeded

# List secrets
az keyvault secret list --vault-name dg-backend-kv-v01 --output table
```

### Container Registry

```bash
# Check ACR status
az acr show \
  --name acrdgbackendv01 \
  --resource-group draftgenie-rg \
  --query "provisioningState" --output tsv

# Expected: Succeeded

# List images
az acr repository list --name acrdgbackendv01 --output table
```

### Container Apps Environment

```bash
# Check environment status
az containerapp env show \
  --name dg-backend-env \
  --resource-group draftgenie-rg \
  --query "properties.provisioningState" --output tsv

# Expected: Succeeded
```

---

## 🔄 Service Management

### Restart Service

```bash
# Restart a service
az containerapp revision restart \
  --name api-gateway \
  --resource-group draftgenie-rg
```

### Update Environment Variables

```bash
# Update a single environment variable
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --set-env-vars "NEW_VAR=value"

# Update multiple environment variables
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --set-env-vars \
    "VAR1=value1" \
    "VAR2=value2"
```

### Scale Service

```bash
# Scale to specific number of replicas
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --min-replicas 2 \
  --max-replicas 10
```

---

## 🐛 Troubleshooting

### Service Not Responding

```bash
# 1. Check service status
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.runningStatus" --output tsv

# 2. Check replicas
az containerapp replica list --name api-gateway --resource-group draftgenie-rg

# 3. View recent logs
az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 100

# 4. Check environment variables
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.template.containers[0].env" --output json | jq .
```

### Database Connection Issues

```bash
# 1. Check PostgreSQL status
az postgres flexible-server show \
  --name dg-backend-postgres \
  --resource-group draftgenie-rg

# 2. Check firewall rules
az postgres flexible-server firewall-rule list \
  --name dg-backend-postgres \
  --resource-group draftgenie-rg \
  --output table

# 3. Check if DATABASE_URL is set in service
az containerapp show --name speaker-service --resource-group draftgenie-rg \
  --query "properties.template.containers[0].env[?name=='DATABASE_URL']" --output json
```

### Service Communication Issues

```bash
# 1. Check if services are in same environment
az containerapp list --resource-group draftgenie-rg \
  --query "[].{Name:name, Environment:properties.environmentId}" --output table

# 2. Check service URLs in API Gateway
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.template.containers[0].env[?contains(name, 'SERVICE_URL')]" --output json

# 3. Test internal service connectivity (from API Gateway logs)
az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 100 | grep -i "connection\|error"
```

---

## 📈 Performance Testing

### Response Time Test

```bash
# Test API Gateway response time
time curl -s https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health > /dev/null

# Multiple requests
for i in {1..10}; do
  time curl -s https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health > /dev/null
done
```

### Load Test (Simple)

```bash
# Install Apache Bench (if not installed)
# brew install httpd (macOS)
# sudo apt-get install apache2-utils (Ubuntu)

# Run 100 requests with 10 concurrent
ab -n 100 -c 10 https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health
```

---

## 📋 Test Checklist

Use this checklist after deployment or updates:

- [ ] All infrastructure services are healthy (PostgreSQL, Redis, Key Vault, ACR)
- [ ] Container Apps Environment is ready
- [ ] All container apps are running
- [ ] All services have at least 1 replica
- [ ] API Gateway is accessible from internet
- [ ] API Gateway health endpoint returns 200
- [ ] Backend services health endpoint returns 200
- [ ] Swagger documentation is accessible
- [ ] Environment variables are configured
- [ ] Services can connect to databases
- [ ] Services can communicate with each other
- [ ] Logs show no critical errors

---

## 🔗 Quick Links

- **API Gateway:** https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io
- **Swagger Docs:** https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs
- **Azure Portal:** https://portal.azure.com
- **Resource Group:** draftgenie-rg (South India)

---

## 📚 Related Documentation

- [Azure Deployment Test Results](../../AZURE_DEPLOYMENT_TEST_RESULTS.md)
- [Azure Testing Summary](../../AZURE_TESTING_SUMMARY.md)
- [Testing Guide](./TESTING_GUIDE.md)
- [Deployment Guide](../../docs/deployment/azure-deployment-guide.md)

---

**Last Updated:** 2025-10-16  
**Version:** 1.0

