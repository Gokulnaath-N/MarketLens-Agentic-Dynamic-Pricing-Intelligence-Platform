# Development Setup Guide (Windows PowerShell)

This guide documents the verified setup procedure for developing, testing, and running **MarketLens AI** in a Windows environment using PowerShell.

---

## 1. Prerequisites Verification

Before starting, verify that Python (3.10+) and Git are installed and available on your system path:

```powershell
# Check Python version (3.10 to 3.13 supported)
python --version

# Check Git version
git --version
```

---

## 2. Environment Initialization

To avoid contaminating global Python packages, all development should occur inside an isolated virtual environment (`.venv`):

```powershell
# Ensure you are at the project root
cd "d:\Professional Projects\Agentic_Dynammic_Intelligence_Platform"

# Create a local virtual environment named .venv
python -m venv .venv

# Enable script execution if restricted (run in PowerShell if necessary)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

Once activated, your terminal prompt will be prefixed with `(.venv)`.

---

## 3. Package Installation

Install the package in **editable mode** with core runtime dependencies and development dependencies (`pytest`):

```powershell
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install marketlens-ai in editable mode with development extras
pip install -e ".[dev]"
```

*Note on Optional Dependency Groups:*  
As the project progresses through subsequent phases, additional components can be installed on demand:
- **Data Engineering:** `pip install -e ".[data]"`
- **Forecasting Models:** `pip install -e ".[forecasting]"`
- **FastAPI Backend:** `pip install -e ".[api]"`
- **Streamlit Dashboard:** `pip install -e ".[dashboard]"`
- **All modules:** `pip install -e ".[all]"`

---

## 4. Environment Variables Configuration

Copy the example environment configuration to `.env`:

```powershell
Copy-Item .env.example .env
```

Review `.env` to configure optional local overrides (such as `MARKETLENS_LOG_LEVEL=DEBUG`). In Phase 0, no external API keys or credentials are required.

---

## 5. Verification & Testing

Verify that the installation was successful and all unit tests pass:

```powershell
# Run the test suite using pytest
python -m pytest

# Run with verbose output and summary
python -m pytest -v

# Smoke-test configuration loading
python -c "from marketlens.config import load_yaml_config; print(load_yaml_config('app.yaml'))"
```

---

## 6. Git Commit Guidance for Beginners

When completing a development phase or an assigned milestone, follow this standard Git workflow to review, stage, and commit your changes:

```powershell
# 1. Review status of untracked and modified files
git status

# 2. Review git diff (ensure no credentials or raw data are staged)
git diff

# 3. Stage all verified files (respecting .gitignore)
git add .

# 4. Commit your changes with a clear, descriptive message
git commit -m "feat: complete Phase 0 repository foundation and environment setup"

# 5. Push to GitHub (when remote is configured)
# git push origin main
```
