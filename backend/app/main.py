"""DepthWizard FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.api.routes import router as api_router
from app.services.project_manager import ProjectManager
from app.services.job_manager import JobManager

logger = logging.getLogger(__name__)

# Application state
project_manager: ProjectManager | None = None
job_manager: JobManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    global project_manager, job_manager

    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Models directory: {settings.models_dir}")
    logger.info(f"Device: {settings.device}")

    # Initialize managers
    project_manager = ProjectManager(settings)
    job_manager = JobManager(settings)

    # Store in app state for dependency injection
    app.state.settings = settings
    app.state.project_manager = project_manager
    app.state.job_manager = job_manager

    logger.info("DepthWizard ready.")
    yield

    # Shutdown
    logger.info("Shutting down DepthWizard...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Single-View Height Estimation and 3D Flythrough",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router, prefix="/api")

    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "app": settings.app_name, "version": settings.app_version}

    return app


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = create_app()
