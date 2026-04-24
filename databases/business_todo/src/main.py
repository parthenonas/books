from fastapi import FastAPI

from databases.business_todo.src.api.v1.router import api_router

app = FastAPI(
    title="Business Todo API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}

# uvicorn databases.business_todo.src.main:app --reload --host 0.0.0.0 --port 8000
