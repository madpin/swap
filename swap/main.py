from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from swap.scheduler import scheduler
from swap.scheduler.scheduler import start_scheduler, stop_scheduler
from swap.api.v1.endpoints import router as api_router
from swap.utils.logger import logger
from swap.core.database import check_database_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    logger.info("Starting S.W.A.P application")
    
    # Check database health
    if not check_database_health():
        logger.error("Database health check failed")
        raise RuntimeError("Database is not available")
    
    # Start the scheduler
    start_scheduler()
    
    yield
    
    # Cleanup
    logger.info("Shutting down S.W.A.P application")
    stop_scheduler()


app = FastAPI(
    title="S.W.A.P API",
    description="Shift-Workers Arrangement Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = check_database_health()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected"
    }
