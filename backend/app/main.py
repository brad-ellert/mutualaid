import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.db import base  # noqa: F401 - This is needed to create database tables

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API for MutualAid - A community support network",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Set up CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Set up static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up...")
        # Initialize database
        db = SessionLocal()
        try:
            # Create database tables
            from app.db import base
            base.Base.metadata.create_all(bind=db.connection().engine)
        finally:
            db.close()

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down...")

    @app.get("/")
    async def root():
        return {
            "message": "Welcome to MutualAid API",
            "version": settings.VERSION,
            "docs": "/docs",
        }

    return app

# Create the FastAPI application
app = create_application()
