#!/bin/bash
# DraftGenie Deployment Scripts - Virtual Environment Setup
#
# This script sets up a Python virtual environment and installs all
# necessary dependencies for running the Azure deployment scripts.
#
# Usage:
#   bash scripts/setup-venv.sh
#   or
#   ./scripts/setup-venv.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
GITIGNORE_FILE="$PROJECT_ROOT/.gitignore"

# Print functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_step() {
    echo ""
    echo -e "${BLUE}[$1] $2${NC}"
}

# Main script
print_header "DraftGenie - Virtual Environment Setup"

# Step 1: Check Python installation
print_step "1/7" "Checking Python installation"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    echo ""
    echo "Please install Python 3.8 or higher:"
    echo "  macOS:   brew install python3"
    echo "  Ubuntu:  sudo apt-get install python3 python3-pip python3-venv"
    echo "  Fedora:  sudo dnf install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

print_success "Python $PYTHON_VERSION found"

# Step 2: Check if venv module is available
print_step "2/7" "Checking venv module"

if ! python3 -m venv --help &> /dev/null; then
    print_error "Python venv module is not available"
    echo ""
    echo "Please install python3-venv:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-venv"
    echo "  Fedora:        sudo dnf install python3-venv"
    exit 1
fi

print_success "venv module is available"

# Step 3: Check if virtual environment already exists
print_step "3/7" "Checking for existing virtual environment"

if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists at: $VENV_DIR"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
        print_success "Removed existing virtual environment"
    else
        print_info "Using existing virtual environment"
        SKIP_CREATE=true
    fi
else
    print_info "No existing virtual environment found"
fi

# Step 4: Create virtual environment
if [ "$SKIP_CREATE" != "true" ]; then
    print_step "4/7" "Creating virtual environment"
    
    if python3 -m venv "$VENV_DIR"; then
        print_success "Virtual environment created at: $VENV_DIR"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
else
    print_step "4/7" "Skipping virtual environment creation"
fi

# Step 5: Activate virtual environment and install dependencies
print_step "5/7" "Installing dependencies"

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
else
    print_error "Failed to find activation script"
    exit 1
fi

# Upgrade pip
print_info "Upgrading pip..."
if python -m pip install --upgrade pip --quiet; then
    print_success "pip upgraded"
else
    print_warning "Failed to upgrade pip (continuing anyway)"
fi

# Install requirements
if [ -f "$REQUIREMENTS_FILE" ]; then
    print_info "Installing packages from requirements.txt..."
    if pip install -r "$REQUIREMENTS_FILE" --quiet; then
        print_success "All dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        deactivate
        exit 1
    fi
else
    print_warning "requirements.txt not found at: $REQUIREMENTS_FILE"
    print_info "Installing PyYAML manually..."
    if pip install PyYAML --quiet; then
        print_success "PyYAML installed"
    else
        print_error "Failed to install PyYAML"
        deactivate
        exit 1
    fi
fi

# Step 6: Verify installation
print_step "6/7" "Verifying installation"

VERIFICATION_FAILED=false

# Check PyYAML
if python -c "import yaml" 2>/dev/null; then
    YAML_VERSION=$(python -c "import yaml; print(yaml.__version__)" 2>/dev/null)
    print_success "PyYAML $YAML_VERSION installed"
else
    print_error "PyYAML not found"
    VERIFICATION_FAILED=true
fi

# Check if deployment script exists
if [ -f "$SCRIPT_DIR/deploy-azure.py" ]; then
    print_success "deploy-azure.py found"
else
    print_warning "deploy-azure.py not found (expected at: $SCRIPT_DIR/deploy-azure.py)"
fi

# Check if azure modules exist
if [ -d "$SCRIPT_DIR/azure" ]; then
    print_success "Azure deployment modules found"
else
    print_warning "Azure deployment modules not found"
fi

if [ "$VERIFICATION_FAILED" = true ]; then
    print_error "Verification failed"
    deactivate
    exit 1
fi

# Step 7: Update .gitignore
print_step "7/7" "Updating .gitignore"

if [ -f "$GITIGNORE_FILE" ]; then
    if grep -q "scripts/venv" "$GITIGNORE_FILE" 2>/dev/null; then
        print_info ".gitignore already contains scripts/venv"
    else
        echo "" >> "$GITIGNORE_FILE"
        echo "# Python virtual environment for deployment scripts" >> "$GITIGNORE_FILE"
        echo "scripts/venv/" >> "$GITIGNORE_FILE"
        print_success "Added scripts/venv/ to .gitignore"
    fi
else
    print_warning ".gitignore not found, creating one..."
    cat > "$GITIGNORE_FILE" << EOF
# Python virtual environment for deployment scripts
scripts/venv/
EOF
    print_success "Created .gitignore with scripts/venv/"
fi

# Deactivate virtual environment
deactivate

# Success message
print_header "Setup Complete!"

echo -e "${GREEN}Virtual environment successfully created and configured!${NC}"
echo ""
echo "📁 Location: $VENV_DIR"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Activate the virtual environment:"
echo -e "   ${BLUE}source scripts/venv/bin/activate${NC}"
echo ""
echo "2. Run the Azure deployment script:"
echo -e "   ${BLUE}python scripts/deploy-azure.py${NC}"
echo ""
echo "   Or use the interactive setup:"
echo -e "   ${BLUE}bash scripts/azure/setup.sh${NC}"
echo ""
echo "3. When done, deactivate the virtual environment:"
echo -e "   ${BLUE}deactivate${NC}"
echo ""
echo "💡 Tips:"
echo "   - The virtual environment keeps dependencies isolated"
echo "   - You can delete scripts/venv/ and re-run this script anytime"
echo "   - The virtual environment is automatically excluded from git"
echo ""
echo "📚 Documentation:"
echo "   - Quick Start: scripts/azure/QUICKSTART.md"
echo "   - Full Guide:  scripts/azure/README.md"
echo ""
echo -e "${GREEN}Happy deploying! 🎉${NC}"
echo ""

