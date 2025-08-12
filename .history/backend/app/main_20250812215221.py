from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.monitor import monitoring_service
from api.routes import services, monitoring, logs, config, websocket, alerts


# Create FastAPI app
app = FastAPI(
    title="KbEye API",
    description="Microservices monitoring dashboard API",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start monitoring when app starts"""
    import asyncio
    # Create task in background without awaiting
    task = asyncio.create_task(monitoring_service.start_monitoring())
    # Don't await the task, let it run in background

@app.on_event("shutdown")
async def shutdown_event():
    """Stop monitoring when app shuts down"""
    monitoring_service.stop_monitoring()

# Include routers
app.include_router(services.router)
app.include_router(monitoring.router)
app.include_router(logs.router)
app.include_router(config.router)
app.include_router(websocket.router)
app.include_router(alerts.router)

@app.get("/")
async def root():
    return {"message": "KbEye API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "kbeye-api"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)