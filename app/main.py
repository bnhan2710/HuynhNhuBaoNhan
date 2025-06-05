# Entry point for FastAPI app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="Message System API",
    description="A messaging system API with user management and message functionality",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Message System API"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok"}
