"""IlmuAI FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.database import init_db
from app.core.redis import init_redis, close_redis
from app.core.exceptions import IlmuAIException
from app.routers import auth, chat, conversations, bookmarks

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting IlmuAI API...")
    try:
        await init_db()
        logger.info("Database connected")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")

    try:
        await init_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    logger.info("IlmuAI API started successfully")
    yield

    # Shutdown
    logger.info("Shutting down IlmuAI API...")
    await close_redis()
    logger.info("IlmuAI API shutdown complete")


app = FastAPI(
    title="IlmuAI API",
    description="AI-powered Islamic Knowledge Platform for Malaysian Muslims",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(IlmuAIException)
async def ilmuai_exception_handler(request: Request, exc: IlmuAIException):
    """Handle custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "IlmuAI API",
        "version": "0.1.0",
        "description": "AI-powered Islamic Knowledge Platform",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }
