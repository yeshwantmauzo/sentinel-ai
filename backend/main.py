from fastapi import FastAPI

app = FastAPI(title="Sentinel AI API")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "sentinel-api"}