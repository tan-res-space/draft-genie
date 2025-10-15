# Python Virtual Environment Guide

This guide explains how to use Python virtual environments with the DraftGenie deployment scripts.

## What is a Virtual Environment?

A Python virtual environment is an isolated Python environment that:

- ✅ **Isolates dependencies** - Keeps project dependencies separate from system Python
- ✅ **Prevents conflicts** - Avoids version conflicts between different projects
- ✅ **Easy to recreate** - Can be deleted and recreated anytime
- ✅ **Portable** - Can be recreated on any machine with the same dependencies
- ✅ **Clean** - Doesn't pollute your system Python installation

## Quick Start

### 1. Create Virtual Environment

```bash
# Run the setup script
bash scripts/setup-venv.sh
```

This will:
- Create a virtual environment in `scripts/venv/`
- Install all required dependencies (PyYAML)
- Add `scripts/venv/` to `.gitignore`
- Verify the installation

### 2. Activate Virtual Environment

```bash
# Option 1: Direct activation
source scripts/venv/bin/activate

# Option 2: Using helper script
source scripts/activate-venv.sh
```

You'll see `(venv)` in your terminal prompt when activated.

### 3. Run Deployment Scripts

```bash
# Now you can run the deployment scripts
python scripts/deploy-azure.py

# Or use the setup wizard
bash scripts/azure/setup.sh
```

### 4. Deactivate When Done

```bash
deactivate
```

## Detailed Usage

### Creating the Virtual Environment

The `setup-venv.sh` script performs these steps:

1. **Checks Python version** - Requires Python 3.8+
2. **Checks venv module** - Ensures venv is available
3. **Creates virtual environment** - In `scripts/venv/`
4. **Upgrades pip** - To latest version
5. **Installs dependencies** - From `requirements.txt`
6. **Verifies installation** - Checks all packages
7. **Updates .gitignore** - Excludes venv from git

**Example:**

```bash
$ bash scripts/setup-venv.sh

========================================
DraftGenie - Virtual Environment Setup
========================================

[1/7] Checking Python installation
✓ Python 3.9.6 found

[2/7] Checking venv module
✓ venv module is available

[3/7] Checking for existing virtual environment
ℹ No existing virtual environment found

[4/7] Creating virtual environment
✓ Virtual environment created at: /path/to/scripts/venv

[5/7] Installing dependencies
✓ Virtual environment activated
✓ pip upgraded
✓ All dependencies installed successfully

[6/7] Verifying installation
✓ PyYAML 6.0.3 installed
✓ deploy-azure.py found
✓ Azure deployment modules found

[7/7] Updating .gitignore
✓ Added scripts/venv/ to .gitignore

========================================
Setup Complete!
========================================
```

### Activating the Virtual Environment

**Method 1: Direct Activation**

```bash
source scripts/venv/bin/activate
```

**Method 2: Using Helper Script**

```bash
source scripts/activate-venv.sh
```

The helper script provides:
- Checks if virtual environment exists
- Warns if already activated
- Shows Python version after activation
- Provides deactivation instructions

**Example:**

```bash
$ source scripts/activate-venv.sh
✓ Virtual environment activated

Python: /path/to/scripts/venv/bin/python
Version: Python 3.9.6

To deactivate when done:
  deactivate
```

### Verifying Activation

When the virtual environment is active:

```bash
# Check Python location (should be in venv/)
which python
# Output: /path/to/scripts/venv/bin/python

# Check installed packages
pip list

# Check specific package
python -c "import yaml; print(yaml.__version__)"
```

### Deactivating the Virtual Environment

```bash
deactivate
```

This returns you to your system Python.

## Common Workflows

### First-Time Setup

```bash
# 1. Create virtual environment
bash scripts/setup-venv.sh

# 2. Activate it
source scripts/venv/bin/activate

# 3. Run deployment
python scripts/deploy-azure.py

# 4. Deactivate when done
deactivate
```

### Subsequent Uses

```bash
# Activate virtual environment
source scripts/venv/bin/activate

# Run deployment
python scripts/deploy-azure.py

# Deactivate
deactivate
```

### Recreating Virtual Environment

If something goes wrong:

```bash
# Delete existing virtual environment
rm -rf scripts/venv

# Recreate it
bash scripts/setup-venv.sh
```

## Troubleshooting

### Issue: "venv module not available"

**Solution for Ubuntu/Debian:**
```bash
sudo apt-get install python3-venv
```

**Solution for Fedora:**
```bash
sudo dnf install python3-venv
```

### Issue: "Virtual environment already exists"

The setup script will ask if you want to recreate it:

```bash
$ bash scripts/setup-venv.sh
⚠ Virtual environment already exists at: /path/to/scripts/venv
Do you want to recreate it? (y/N):
```

- Type `y` to recreate
- Type `n` to keep existing

### Issue: "This script must be sourced"

When activating, use `source` or `.`:

```bash
# ✓ Correct
source scripts/activate-venv.sh

# ✗ Wrong
bash scripts/activate-venv.sh
```

### Issue: "Another virtual environment is active"

Deactivate the current one first:

```bash
deactivate
source scripts/venv/bin/activate
```

### Issue: "Permission denied"

Make scripts executable:

```bash
chmod +x scripts/setup-venv.sh
chmod +x scripts/activate-venv.sh
```

## Advanced Usage

### Installing Additional Packages

```bash
# Activate virtual environment
source scripts/venv/bin/activate

# Install package
pip install package-name

# Update requirements.txt (optional)
pip freeze > scripts/requirements.txt

# Deactivate
deactivate
```

### Using Different Python Versions

```bash
# Create venv with specific Python version
python3.9 -m venv scripts/venv

# Or
python3.10 -m venv scripts/venv
```

### Checking Virtual Environment Status

```bash
# Check if in virtual environment
echo $VIRTUAL_ENV

# If active, shows path to venv
# If not active, shows nothing
```

## Integration with Deployment Scripts

The deployment scripts work seamlessly with or without virtual environments:

### With Virtual Environment

```bash
source scripts/venv/bin/activate
python scripts/deploy-azure.py
deactivate
```

### Without Virtual Environment

```bash
# Install dependencies globally
pip3 install PyYAML

# Run deployment
python3 scripts/deploy-azure.py
```

## Best Practices

1. **Always use virtual environments** for Python projects
2. **Activate before running scripts** to ensure correct dependencies
3. **Deactivate when done** to return to system Python
4. **Don't commit venv/** to git (already in .gitignore)
5. **Recreate if issues arise** - it's quick and safe

## Files Created

The virtual environment setup creates:

```
scripts/
├── venv/                    # Virtual environment (excluded from git)
│   ├── bin/                # Executables (python, pip, etc.)
│   ├── lib/                # Installed packages
│   └── pyvenv.cfg          # Configuration
├── setup-venv.sh           # Setup script
└── activate-venv.sh        # Activation helper
```

## Comparison: Virtual Environment vs Global

| Aspect | Virtual Environment | Global Installation |
|--------|-------------------|-------------------|
| **Isolation** | ✅ Isolated | ❌ Shared |
| **Conflicts** | ✅ No conflicts | ⚠️ Possible |
| **Cleanup** | ✅ Easy (delete folder) | ❌ Manual |
| **Portability** | ✅ Reproducible | ⚠️ Varies |
| **Setup Time** | ~30 seconds | ~10 seconds |
| **Disk Space** | ~20-50 MB | Minimal |
| **Recommended** | ✅ Yes | ⚠️ For quick tests |

## Summary

Virtual environments are the recommended way to run the DraftGenie deployment scripts. They provide isolation, prevent conflicts, and are easy to manage.

**Quick Commands:**

```bash
# Setup (once)
bash scripts/setup-venv.sh

# Activate (each session)
source scripts/venv/bin/activate

# Run scripts
python scripts/deploy-azure.py

# Deactivate (when done)
deactivate
```

For more information, see:
- [Python venv documentation](https://docs.python.org/3/library/venv.html)
- [Azure Deployment Guide](azure/README.md)
- [Quick Start Guide](azure/QUICKSTART.md)

