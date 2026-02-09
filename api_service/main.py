"""FastAPI Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api_service.config import api_config
from api_service.services.logging_service import setup_logging
from api_service.routers import nlp, queries, feedback, health, voice
from nlp_service.retrieval import get_retrieval_system
import structlog

# Setup logging
setup_logging(api_config.log_level)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting NLP service", version=api_config.api_version)
    
    try:
        # Initialize retrieval system
        logger.info("Initializing retrieval system...")
        retrieval_system = await get_retrieval_system()
        logger.info("Retrieval system initialized", 
                   doc_count=len(retrieval_system.documents))
        
        # Initialize NLP models (lazy loading on first use)
        logger.info("NLP models will be loaded on first request")
        
        logger.info("NLP service started successfully")
        
    except Exception as e:
        logger.error("Failed to start NLP service", error=str(e), exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down NLP service")


# Create FastAPI app
app = FastAPI(
    title=api_config.api_title,
    description=api_config.api_description,
    version=api_config.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config.cors_origins,
    allow_credentials=api_config.cors_credentials,
    allow_methods=api_config.cors_methods,
    allow_headers=api_config.cors_headers,
)

# Include routers
app.include_router(health.router)
app.include_router(nlp.router)
app.include_router(voice.router)
app.include_router(queries.router)
app.include_router(feedback.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Retail Intelligence NLP Service",
        "version": api_config.api_version,
        "status": "running",
        "docs": "/docs"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", 
                error=str(exc), 
                path=request.url.path,
                exc_info=True)
    
    return {
        "error": "An unexpected error occurred",
        "detail": str(exc) if api_config.log_level == "DEBUG" else "Internal server error"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_service.main:app",
        host=api_config.api_host,
        port=api_config.api_port,
        reload=api_config.api_reload,
        log_level=api_config.log_level.lower()
    )
