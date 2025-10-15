# DraftGenie Deployment Guides

This directory contains comprehensive, beginner-friendly deployment guides for deploying DraftGenie to three major cloud platforms.

## Available Deployment Guides

### 1. [Microsoft Azure Deployment Guide](./azure-deployment-guide.md)
Deploy DraftGenie to Microsoft Azure using Azure Container Apps, Cloud SQL, and other managed services.

**Best for:**
- Enterprise environments
- Organizations already using Microsoft ecosystem
- Need for strong compliance and security features
- Integration with Azure Active Directory

**Estimated Cost:** $93-143/month

**Key Services:**
- Azure Container Apps (serverless containers)
- Azure Database for PostgreSQL
- Azure Cache for Redis
- MongoDB Atlas on Azure
- Azure Container Registry
- Azure Key Vault

---

### 2. [Google Cloud Platform (GCP) Deployment Guide](./gcp-deployment-guide.md)
Deploy DraftGenie to Google Cloud Platform using Cloud Run, Cloud SQL, and other managed services.

**Best for:**
- Startups and scale-ups
- Organizations using Google Workspace
- Need for cost-effective serverless architecture
- Integration with Google AI/ML services (Gemini API)

**Estimated Cost:** $77-102/month

**Key Services:**
- Cloud Run (fully managed serverless)
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- MongoDB Atlas on GCP
- Artifact Registry
- Secret Manager

---

### 3. [Zoho Cloud Deployment Guide](./zoho-deployment-guide.md)
Deploy DraftGenie using a hybrid approach with Zoho Catalyst and complementary managed services.

**Best for:**
- Small projects and MVPs
- Organizations already using Zoho ecosystem
- Budget-conscious deployments
- Development and testing environments

**Estimated Cost:** $0-10/month (free tiers), $100-200/month (production)

**Key Services:**
- Zoho Catalyst (serverless functions)
- Render.com (PostgreSQL, Python services)
- MongoDB Atlas
- Upstash (serverless Redis)
- CloudAMQP (managed RabbitMQ)

---

## Quick Comparison

| Feature | Azure | GCP | Zoho (Hybrid) |
|---------|-------|-----|---------------|
| **Deployment Complexity** | Medium | Medium | Medium-High |
| **Free Tier** | $200 credit (30 days) | $300 credit (90 days) | Multiple free tiers |
| **Monthly Cost (Dev)** | $93-143 | $77-102 | $0-10 |
| **Monthly Cost (Prod)** | $150-300 | $120-250 | $100-200 |
| **Auto-Scaling** | ✅ Excellent | ✅ Excellent | ⚠️ Limited |
| **Cold Starts** | ❌ Minimal | ❌ Minimal | ⚠️ Yes (free tier) |
| **Managed Services** | ✅ Comprehensive | ✅ Comprehensive | ⚠️ Hybrid approach |
| **Global Reach** | ✅ 60+ regions | ✅ 35+ regions | ⚠️ Limited |
| **Enterprise Support** | ✅ Excellent | ✅ Excellent | ⚠️ Limited |
| **Best For** | Enterprise | Startups | Small projects |

---

## Choosing the Right Platform

### Choose **Azure** if:
- ✅ Your organization uses Microsoft products (Office 365, Teams, etc.)
- ✅ You need enterprise-grade compliance (HIPAA, SOC 2, etc.)
- ✅ You require Azure Active Directory integration
- ✅ You have existing Azure credits or enterprise agreement
- ✅ You need strong hybrid cloud capabilities

### Choose **GCP** if:
- ✅ You want the most cost-effective serverless solution
- ✅ You're already using Google Workspace or Google services
- ✅ You need tight integration with Google AI/ML services
- ✅ You prefer Google's developer experience and tools
- ✅ You want scale-to-zero capabilities to minimize costs
- ✅ You're building a startup or scale-up

### Choose **Zoho Cloud (Hybrid)** if:
- ✅ You're building an MVP or proof of concept
- ✅ You want to minimize costs during development
- ✅ Your organization already uses Zoho products
- ✅ You're comfortable managing multiple platform accounts
- ✅ You don't need enterprise-scale performance yet
- ✅ You plan to migrate to Azure/GCP later for production

---

## What's Included in Each Guide

All three deployment guides include:

1. **Prerequisites**
   - Required accounts and subscriptions
   - Tool installation instructions
   - Verification steps

2. **Architecture Overview**
   - Service mapping diagrams
   - Technology stack explanation
   - Cost breakdown

3. **Step-by-Step Deployment**
   - Detailed, numbered instructions
   - Copy-paste ready commands
   - Explanations of what each step does

4. **Environment Variables & Secrets**
   - Secrets management best practices
   - Required variables for each service
   - Security considerations

5. **Domain & SSL Configuration**
   - Custom domain setup
   - SSL certificate management
   - DNS configuration

6. **Monitoring & Logging**
   - Log viewing and aggregation
   - Metrics and dashboards
   - Alert configuration

7. **Cost Optimization**
   - Detailed cost breakdown
   - Free tier maximization
   - Cost-saving tips

8. **Troubleshooting**
   - Common issues and solutions
   - Diagnostic commands
   - Getting help resources

---

## General Prerequisites

Regardless of which platform you choose, you'll need:

1. **Google Gemini API Key**
   - Get from: https://makersuite.google.com/app/apikey
   - Free tier: 60 requests per minute
   - Required for AI-powered features

2. **Local Development Tools**
   - Git (for cloning the repository)
   - Docker (for building container images)
   - Node.js 18+ (for some CLI tools)

3. **Basic Knowledge**
   - Command line / terminal usage
   - Basic understanding of environment variables
   - Familiarity with Git

---

## Deployment Time Estimates

| Platform | First-Time Deployment | Subsequent Deployments |
|----------|----------------------|------------------------|
| Azure | 2-3 hours | 30-45 minutes |
| GCP | 2-3 hours | 30-45 minutes |
| Zoho (Hybrid) | 3-4 hours | 45-60 minutes |

**Note:** Times assume you have all prerequisites ready and accounts created.

---

## Architecture Overview

DraftGenie consists of:

### Application Services (5)
1. **API Gateway** (Node.js/NestJS) - Main entry point, routing, authentication
2. **Speaker Service** (Node.js/NestJS) - Speaker management, metadata
3. **Draft Service** (Python/FastAPI) - Draft ingestion, NLP, correction vectors
4. **RAG Service** (Python/FastAPI) - AI-powered draft generation with LangChain
5. **Evaluation Service** (Python/FastAPI) - Metrics calculation, quality scoring

### Infrastructure Services (5)
1. **PostgreSQL** - Relational data (speakers, evaluations)
2. **MongoDB** - Document storage (drafts, generated content)
3. **Qdrant** - Vector database (correction vectors, embeddings)
4. **Redis** - Caching and session management
5. **RabbitMQ** - Message queue for event-driven architecture

---

## Support and Resources

### Documentation
- **Main README**: [../../README.md](../../README.md)
- **System Architecture**: [../system_architecture_and_implementation_plan.md](../system_architecture_and_implementation_plan.md)
- **Getting Started**: [../../GETTING_STARTED.md](../../GETTING_STARTED.md)

### Community
- **GitHub Issues**: https://github.com/tan-res-space/draft-genie/issues
- **Discussions**: https://github.com/tan-res-space/draft-genie/discussions

### Platform-Specific Support
- **Azure**: https://azure.microsoft.com/support/
- **GCP**: https://cloud.google.com/support
- **Zoho**: https://catalyst.zoho.com/support

---

## Migration Between Platforms

If you start with one platform and want to migrate to another:

### From Zoho to Azure/GCP
1. Export data from MongoDB Atlas (same for all platforms)
2. Export PostgreSQL data: `pg_dump $POSTGRES_URL > backup.sql`
3. Follow the target platform's deployment guide
4. Import data to new databases
5. Update DNS to point to new deployment
6. Monitor for 24-48 hours before decommissioning old deployment

### From Azure to GCP (or vice versa)
1. Deploy to new platform following the guide
2. Set up database replication (if needed for zero-downtime)
3. Export/import data
4. Update DNS with low TTL
5. Switch traffic to new platform
6. Monitor and verify
7. Decommission old deployment

---

## Contributing

Found an issue with a deployment guide? Want to add a guide for another platform?

1. Open an issue describing the problem or suggestion
2. Submit a pull request with improvements
3. Follow the existing guide structure and style

---

## License

These deployment guides are part of the DraftGenie project and follow the same license.

---

## Changelog

### 2024-01-15
- ✅ Initial release of all three deployment guides
- ✅ Azure deployment guide completed
- ✅ GCP deployment guide completed
- ✅ Zoho Cloud (hybrid) deployment guide completed
- ✅ Comprehensive troubleshooting sections added
- ✅ Cost optimization tips included
- ✅ Beginner-friendly explanations throughout

---

## Quick Start

1. **Choose your platform** using the comparison table above
2. **Open the corresponding guide**:
   - [Azure Deployment Guide](./azure-deployment-guide.md)
   - [GCP Deployment Guide](./gcp-deployment-guide.md)
   - [Zoho Deployment Guide](./zoho-deployment-guide.md)
3. **Follow the step-by-step instructions**
4. **Verify your deployment** using the health check endpoints
5. **Set up monitoring and alerts**
6. **Optimize costs** using the tips in each guide

---

## Need Help?

If you encounter issues:

1. Check the **Troubleshooting** section in your platform's guide
2. Search existing **GitHub Issues**
3. Review the **platform-specific documentation**
4. Open a new issue with:
   - Platform you're deploying to
   - Step where you encountered the issue
   - Error messages and logs
   - What you've already tried

---

**Happy Deploying! 🚀**


