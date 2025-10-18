from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.core.database import engine, get_db, init_db
from app.api import auth, chat, integrations, webhooks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Financial Advisor Agent",
    description="AI agent for financial advisors with Gmail, Calendar, and Hubspot integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    logger.info("Starting up application...")
    await init_db()
    logger.info("Database initialized")

@app.get("/")
async def root():
    return {
        "message": "AI Financial Advisor Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

