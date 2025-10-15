# Virtual Environment - Quick Reference

## One-Line Commands

```bash
# Setup (first time only)
bash scripts/setup-venv.sh

# Activate
source scripts/venv/bin/activate

# Activate (with helper)
source scripts/activate-venv.sh

# Deactivate
deactivate

# Recreate
rm -rf scripts/venv && bash scripts/setup-venv.sh

# Check if active
echo $VIRTUAL_ENV
```

---

## Common Workflows

### First Time Setup

```bash
bash scripts/setup-venv.sh
source scripts/venv/bin/activate
python scripts/deploy-azure.py
deactivate
```

### Daily Use

```bash
source scripts/venv/bin/activate
python scripts/deploy-azure.py
deactivate
```

### Troubleshooting

```bash
rm -rf scripts/venv
bash scripts/setup-venv.sh
```

---

## Quick Checks

```bash
# Check Python location
which python

# Check Python version
python --version

# Check installed packages
pip list

# Check specific package
python -c "import yaml; print(yaml.__version__)"

# Check if venv is active
echo $VIRTUAL_ENV
```

---

## File Locations

```
scripts/
├── setup-venv.sh              # Setup script
├── activate-venv.sh           # Activation helper
├── venv/                      # Virtual environment
│   ├── bin/python            # Python interpreter
│   └── bin/activate          # Activation script
└── requirements.txt           # Dependencies
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| venv module not found | `sudo apt-get install python3-venv` |
| Permission denied | `chmod +x scripts/setup-venv.sh` |
| Must be sourced | Use `source` not `bash` |
| Already activated | `deactivate` first |
| Wrong Python version | Use Python 3.8+ |

---

## Documentation

- **Full Guide**: `scripts/VIRTUAL_ENVIRONMENT_GUIDE.md`
- **Summary**: `scripts/VENV_SETUP_SUMMARY.md`
- **Azure Guide**: `scripts/azure/README.md`
- **Quick Start**: `scripts/azure/QUICKSTART.md`

---

## Tips

- ✅ Always activate before running deployment scripts
- ✅ Deactivate when done to return to system Python
- ✅ You'll see `(venv)` in prompt when active
- ✅ Safe to delete and recreate anytime
- ✅ Already excluded from git

---

## Help

```bash
# Setup help
bash scripts/setup-venv.sh --help

# Python venv help
python3 -m venv --help

# Pip help
pip --help
```

