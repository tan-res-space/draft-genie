#!/bin/bash
# DraftGenie - Activate Virtual Environment
#
# This script provides a convenient way to activate the Python virtual environment.
# 
# Usage:
#   source scripts/activate-venv.sh
#   or
#   . scripts/activate-venv.sh
#
# Note: This script must be sourced (not executed) to activate the environment
#       in your current shell.

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo -e "${RED}✗ Error: This script must be sourced, not executed${NC}"
    echo ""
    echo "Usage:"
    echo -e "  ${BLUE}source scripts/activate-venv.sh${NC}"
    echo "  or"
    echo -e "  ${BLUE}. scripts/activate-venv.sh${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}✗ Virtual environment not found at: $VENV_DIR${NC}"
    echo ""
    echo "Create it first by running:"
    echo -e "  ${BLUE}bash scripts/setup-venv.sh${NC}"
    return 1
fi

# Check if already activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    if [[ "$VIRTUAL_ENV" == "$VENV_DIR" ]]; then
        echo -e "${YELLOW}⚠ Virtual environment is already active${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Another virtual environment is active: $VIRTUAL_ENV${NC}"
        echo "Deactivate it first with: deactivate"
        return 1
    fi
fi

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
    echo ""
    echo "Python: $(which python)"
    echo "Version: $(python --version)"
    echo ""
    echo "To deactivate when done:"
    echo -e "  ${BLUE}deactivate${NC}"
else
    echo -e "${RED}✗ Activation script not found${NC}"
    return 1
fi

