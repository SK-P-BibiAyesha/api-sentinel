
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import yaml

from main import compare_apis

app = FastAPI(
    title="API Sentinel",
    description="Detect API drift and backward-compatibility risks",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def read_api_file(file: UploadFile):
    filename = (file.filename or "").lower()

    if not filename.endswith((".yaml", ".yml", ".json")):
        raise HTTPException(
            status_code=400,
            detail="Upload an OpenAPI YAML or JSON file.",
        )

    try:
        content = await file.read()

        if len(content) > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File must be smaller than 2 MB.",
            )

        data = yaml.safe_load(content)

        if not isinstance(data, dict):
            raise ValueError("The document must contain an object.")

        if not isinstance(data.get("info"), dict):
            raise ValueError("Missing OpenAPI info section.")

        if not isinstance(data.get("paths"), dict):
            raise ValueError("Missing OpenAPI paths section.")

        if not str(data.get("openapi", "")).startswith("3."):
            raise ValueError("This prototype supports OpenAPI 3.x.")

        return data

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read API specification: {exc}",
        ) from exc


@app.get("/")
def home():
    return {
        "message": "API Sentinel is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/compare")
async def compare(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
):
    old_api = await read_api_file(old_file)
    new_api = await read_api_file(new_file)

    findings = compare_apis(old_api, new_api)

    breaking_count = sum(
        item["severity"] == "BREAKING"
        for item in findings
    )

    warning_count = sum(
        item["severity"] == "WARNING"
        for item in findings
    )

    return {
        "old_version": old_api["info"].get("version", "unknown"),
        "new_version": new_api["info"].get("version", "unknown"),
        "total_changes": len(findings),
        "breaking_changes": breaking_count,
        "warnings": warning_count,
        "result": "FAIL" if breaking_count or warning_count else "PASS",
        "findings": findings,
    }
