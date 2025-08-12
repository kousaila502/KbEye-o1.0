from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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

@app.get("/")
async def root():
    return {"message": "KbEye API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "kbeye-api"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)