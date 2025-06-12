"""
AI Microservice - Standalone service for all AI-powered functionalities.

This microservice handles:
- Natural Language to SQL conversion
- Code generation
- General chat/conversation
- Intent classification and routing
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import Optional

from .config.settings import get_settings
from .api.routes import router as api_router
from .utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 AI Microservice starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log level: {settings.log_level}")
    
    yield
    
    # Shutdown
    logger.info("🛑 AI Microservice shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="AI Microservice",
        description="Standalone AI service for NL2SQL, Code Generation, and Chat",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "ai-microservice",
            "version": "1.0.0"
        }
    
    @app.get("/")
    async def root():
        """Root endpoint with service information."""
        return {
            "service": "AI Microservice",
            "version": "1.0.0",
            "description": "Standalone AI service for NL2SQL, Code Generation, and Chat",
            "endpoints": {
                "health": "/health",
                "api": "/api/v1",
                "docs": "/docs",
                "ai_process": "/api/v1/ai/process",
                "nl2sql": "/api/v1/nl2sql/convert",
                "code_gen": "/api/v1/code/generate",
                "chat": "/api/v1/chat/respond"
            }
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Different port from main Slack bot
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    ) 