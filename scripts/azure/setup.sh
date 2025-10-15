#!/bin/bash
# DraftGenie Azure Deployment - Quick Setup Script

set -e

echo "========================================="
echo "DraftGenie Azure Deployment Setup"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Check Azure CLI
echo "Checking Azure CLI..."
if ! command -v az &> /dev/null; then
    echo -e "${RED}✗ Azure CLI not found${NC}"
    echo "Please install Azure CLI:"
    echo "  macOS: brew install azure-cli"
    echo "  Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    echo "  Windows: https://aka.ms/installazurecliwindows"
    exit 1
fi

AZ_VERSION=$(az version --query '"azure-cli"' -o tsv)
echo -e "${GREEN}✓ Azure CLI $AZ_VERSION${NC}"

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
echo -e "${GREEN}✓ Docker $DOCKER_VERSION${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon not running${NC}"
    echo "Please start Docker Desktop"
    exit 1
fi

echo -e "${GREEN}✓ Docker daemon running${NC}"

# Check Git
echo "Checking Git..."
if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git not found${NC}"
    echo "Please install Git: https://git-scm.com/"
    exit 1
fi

GIT_VERSION=$(git --version | cut -d' ' -f3)
echo -e "${GREEN}✓ Git $GIT_VERSION${NC}"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."

# Check if virtual environment exists
if [ -d "scripts/venv" ]; then
    echo -e "${GREEN}✓ Virtual environment detected${NC}"
    echo "Using virtual environment for dependencies"

    # Check if we're in the virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo -e "${GREEN}✓ Virtual environment is active${NC}"
    else
        echo -e "${YELLOW}⚠ Virtual environment exists but not activated${NC}"
        echo "To activate: source scripts/venv/bin/activate"
    fi
else
    echo -e "${YELLOW}⚠ No virtual environment found${NC}"
    echo "Tip: Run 'bash scripts/setup-venv.sh' to create one"
    echo "Installing dependencies globally..."
    pip3 install -q PyYAML
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
fi

# Check Azure login
echo ""
echo "Checking Azure login..."
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠ Not logged in to Azure${NC}"
    echo "Please run: az login"
    exit 1
fi

AZURE_USER=$(az account show --query user.name -o tsv)
AZURE_SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${GREEN}✓ Logged in as: $AZURE_USER${NC}"
echo -e "${GREEN}✓ Subscription: $AZURE_SUBSCRIPTION${NC}"

# Create config if it doesn't exist
echo ""
if [ ! -f "scripts/azure/config.yaml" ]; then
    echo "Configuration file not found."
    echo "Would you like to:"
    echo "  1) Run interactive configuration wizard"
    echo "  2) Copy example configuration"
    echo "  3) Exit and configure manually"
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo "Running interactive configuration wizard..."
            python3 scripts/deploy-azure.py
            ;;
        2)
            echo "Copying example configuration..."
            cp scripts/azure/config.example.yaml scripts/azure/config.yaml
            echo -e "${GREEN}✓ Configuration copied to scripts/azure/config.yaml${NC}"
            echo -e "${YELLOW}⚠ Please edit config.yaml and add your Gemini API key${NC}"
            ;;
        3)
            echo "Please create scripts/azure/config.yaml manually"
            echo "You can use scripts/azure/config.template.yaml as a reference"
            exit 0
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}✓ Configuration file found${NC}"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Edit scripts/azure/config.yaml (if needed)"
echo "  2. Run deployment:"
echo "     python3 scripts/deploy-azure.py"
echo ""
echo "For help:"
echo "  python3 scripts/deploy-azure.py --help"
echo ""

