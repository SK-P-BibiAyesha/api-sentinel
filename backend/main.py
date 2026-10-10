
from fastapi import FastAPI

app = FastAPI(
    title="API Drift Detector",
    description="Detect potentially breaking API specification changes.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "API Drift Detector backend is running",
    }
