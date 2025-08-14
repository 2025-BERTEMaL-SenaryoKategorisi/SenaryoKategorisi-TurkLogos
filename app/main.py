"""
Main FastAPI application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Import routes
from app.api import chat, testing, analytics, auth, llm_tools
from app.core.database import engine
from app.models import Base
from app.utils.logger import setup_logging
from app.core.config import settings

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting TürkLogos Agent API...")
    
    # Create database tables with fixed relationships
    # Note: Tables already cleaned manually to avoid dependency conflicts
    Base.metadata.create_all(bind=engine)
    logger.info("📊 Database tables created with enhanced authentication fields")
    
    # Initialize sample data
    from app.services.data_service import initialize_sample_data
    await initialize_sample_data()
    logger.info("📝 Sample data initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down TürkLogos Agent API...")

# FastAPI app
app = FastAPI(
    title="TürkLogos Telecom AI Agent API",
    description="TEKNOFEST 2025 - Autonomous Customer Service Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(testing.router, prefix="/test", tags=["Testing"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(auth.router)
app.include_router(llm_tools.router)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "debug": settings.debug
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TürkLogos Telecom AI Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )