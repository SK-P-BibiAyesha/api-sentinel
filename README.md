# API Drift Detector & Breaking Change Linter

An automated microservice tool that detects API schema drift, identifies backward-compatibility breaking changes across OpenAPI/Swagger specifications, and scores risk for continuous integration.

## Current Project Status
- **Phase:** Foundation & Setup
- **Existing Components:**
  - Base project skeleton (`backend/`, `tests/`, `sample_specs/`, `reports/`)
  - Minimal FastAPI application with `/health` endpoint in `backend/main.py`
  - Python virtual environment (`.venv`) configured with Python 3.13
- **Member 2 Focus Area:** Change Linter & Risk Analysis (Schema diffing, breaking change classification, severity scoring).

---

## Windows Setup Instructions

### 1. Prerequisites
- Python 3.13+ installed on Windows.
- PowerShell or Windows Command Prompt.

### 2. Activate Existing Virtual Environment
Open PowerShell in the project root directory:

```powershell
# In PowerShell:
.\.venv\Scripts\Activate.ps1
```

> **Note:** If PowerShell blocks script execution, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### 3. Install Dependencies
If you need to install or verify the runtime dependencies from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

### 4. Run the Backend Server
Start the FastAPI development server with Uvicorn:

```powershell
uvicorn backend.main:app --reload --port 8000
```

Verify the health check endpoint:
- **URL:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

