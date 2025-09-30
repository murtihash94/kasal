import os
import sys
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy import text

# CRITICAL: Set USE_NULLPOOL BEFORE any database imports to prevent asyncpg connection pool issues
# This must be done before importing any modules that might create database connections
os.environ["USE_NULLPOOL"] = "true"

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path

from src.config.settings import settings
from src.api import api_router
from src.core.logger import LoggerManager
from src.db.session import get_db, async_session_factory
from src.services.scheduler_service import SchedulerService
from src.services.execution_cleanup_service import ExecutionCleanupService
from src.utils.databricks_url_utils import DatabricksURLUtils

# Set up basic logging initially, will be enhanced in lifespan
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set debug flag for seeders
os.environ["SEED_DEBUG"] = "True"

# Disable CrewAI telemetry
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

# Set log directory environment variable
log_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "logs")
os.environ["LOG_DIR"] = log_path
# Create logs directory if it doesn't exist
os.makedirs(log_path, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the FastAPI application.
    
    Handles startup and shutdown events for the application.
    """
    # Initialize the centralized logging system
    log_dir = os.environ.get("LOG_DIR")
    logger_manager = LoggerManager.get_instance(log_dir)
    logger_manager.initialize()
    
    system_logger = logger_manager.system
    system_logger.info(f"Starting application... Logs will be stored in: {log_dir}")
    
    # Validate and fix Databricks environment variables early in startup
    try:
        system_logger.info("Validating Databricks environment configuration...")
        DatabricksURLUtils.validate_and_fix_environment()
    except Exception as e:
        system_logger.warning(f"Error validating Databricks environment: {e}")
    
    # Import needed for DB init
    # pylint: disable=unused-import,import-outside-toplevel
    import src.db.all_models  # noqa
    from src.db.session import init_db
    
    # Initialize database first - this creates both the file and tables
    system_logger.info("Initializing database during lifespan...")
    try:
        await init_db()
        system_logger.info("Database initialization complete")
    except Exception as e:
        system_logger.error(f"Database initialization failed: {str(e)}")
    
    # Now check if database exists and tables are initialized
    scheduler = None
    db_initialized = False
    
    try:
        # Simple check for tables - just check if the database file exists with content
        if str(settings.DATABASE_URI).startswith('sqlite'):
            db_path = settings.SQLITE_DB_PATH
            
            # Get absolute path if relative
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            
            system_logger.info(f"Checking database at: {db_path}")
            
            if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
                # Try to execute a simple query to verify tables
                try:
                    # Direct SQLite check - more reliable than trying to use SQLAlchemy
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
                    if cursor.fetchone():
                        system_logger.info("Database tables verified")
                        db_initialized = True
                    else:
                        system_logger.warning("Database file exists but contains no tables")
                    conn.close()
                except Exception as e:
                    system_logger.warning(f"Error checking database tables: {e}")
            else:
                system_logger.warning(f"Database file doesn't exist or is empty at: {db_path}")
        else:
            # For other database types, try a simple connection
            try:
                async with async_session_factory() as session:
                    await session.execute(text("SELECT 1"))
                    await session.commit()
                    db_initialized = True
                    system_logger.info("Database connection successful")
            except Exception as e:
                system_logger.warning(f"Database connection failed: {e}")
    except Exception as e:
        system_logger.error(f"Error checking database: {e}")
    
    # Clean up stale jobs from previous run
    if db_initialized:
        system_logger.info("Cleaning up stale jobs from previous run...")
        try:
            cleaned_jobs = await ExecutionCleanupService.cleanup_stale_jobs_on_startup()
            if cleaned_jobs > 0:
                system_logger.info(f"Successfully cleaned up {cleaned_jobs} stale jobs")
        except Exception as e:
            system_logger.error(f"Error cleaning up stale jobs: {e}")
            # Don't raise - allow app to start even if cleanup fails
    
    # Run database seeders after DB initialization
    if db_initialized:
        # Import needed for seeders
        # pylint: disable=unused-import,import-outside-toplevel
        from src.seeds.seed_runner import run_all_seeders
        
        # Check if seeding is enabled
        should_seed = settings.AUTO_SEED_DATABASE
        system_logger.info(f"AUTO_SEED_DATABASE setting: {settings.AUTO_SEED_DATABASE}")
        
        # Run seeders if enabled
        if should_seed:
            system_logger.info("Running database seeders...")
            try:
                # Always run seeders in background to avoid blocking startup
                import asyncio
                system_logger.info("Starting seeders in background...")
                
                async def run_seeders_background():
                    try:
                        system_logger.info("Background seeders started...")
                        await run_all_seeders()
                        system_logger.info("Background database seeding completed successfully!")
                    except Exception as e:
                        system_logger.error(f"Error running background seeders: {str(e)}")
                        import traceback
                        error_trace = traceback.format_exc()
                        system_logger.error(f"Background seeder error trace: {error_trace}")
                
                # Create background task
                asyncio.create_task(run_seeders_background())
                system_logger.info("Seeders started in background, application startup continues...")
            except Exception as e:
                system_logger.error(f"Error starting seeders: {str(e)}")
                import traceback
                error_trace = traceback.format_exc()
                system_logger.error(f"Seeder startup error trace: {error_trace}")
                # Don't raise so app can start even if seeding fails
        else:
            system_logger.info("Database seeding skipped (AUTO_SEED_DATABASE is False)")
    else:
        system_logger.warning("Skipping seeding as database is not initialized.")
    
    # Initialize scheduler on startup only if database is initialized
    if db_initialized:
        system_logger.info("Initializing scheduler...")
        try:
            # Get database connection
            db_gen = get_db()
            db = await anext(db_gen)
            
            # Initialize scheduler service
            scheduler = SchedulerService(db)
            await scheduler.start_scheduler()
            system_logger.info("Scheduler started successfully.")
        except Exception as e:
            system_logger.error(f"Failed to start scheduler: {e}")
            # Don't raise here, let the application start without scheduler
    else:
        system_logger.warning("Skipping scheduler initialization. Database not ready.")
    
    system_logger.info("Application startup complete")
    
    try:
        yield
    finally:
        # Clean up running jobs during shutdown
        if db_initialized:
            system_logger.info("Application shutting down, cleaning up running jobs...")
            try:
                cleaned_jobs = await ExecutionCleanupService.cleanup_stale_jobs_on_startup()
                if cleaned_jobs > 0:
                    system_logger.info(f"Cleaned up {cleaned_jobs} running jobs during shutdown")
            except Exception as e:
                system_logger.error(f"Error cleaning up jobs during shutdown: {e}")
        
        # Shutdown scheduler if it was started
        if scheduler:
            system_logger.info("Shutting down scheduler...")
            try:
                await scheduler.shutdown()
                system_logger.info("Scheduler shut down successfully.")
            except Exception as e:
                system_logger.error(f"Error during scheduler shutdown: {e}")
        
        system_logger.info("Application shutdown complete.")

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    # Move API docs to /api-docs
    docs_url="/api-docs" if settings.DOCS_ENABLED else None,
    redoc_url="/api-redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/api-openapi.json" if settings.DOCS_ENABLED else None,
    openapi_version="3.1.0"  # Explicitly set OpenAPI version
)

# Add CORS middleware with explicit allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add user context middleware to extract user tokens from Databricks Apps headers
from src.utils.user_context import user_context_middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=user_context_middleware)

# Include the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint - must be defined before catch-all routes
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

# Setup frontend static files and root route
frontend_static_dir = os.environ.get("FRONTEND_STATIC_DIR")
if frontend_static_dir:
    frontend_static_path = Path(frontend_static_dir)
    
    # Mount static files if they exist
    if frontend_static_path.exists():
        static_dir = frontend_static_path / "static"
        if static_dir.exists():
            logger.info(f"Mounting /static from {static_dir}")
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Serve favicon
        favicon_ico = frontend_static_path / "favicon.ico"
        if favicon_ico.exists():
            @app.get("/favicon.ico")
            async def serve_favicon():
                return FileResponse(str(favicon_ico))
        
        # Serve manifest.json
        manifest_json = frontend_static_path / "manifest.json"
        if manifest_json.exists():
            @app.get("/manifest.json")
            async def serve_manifest():
                return FileResponse(str(manifest_json))
        
        # Serve docs directory
        docs_dir = frontend_static_path / "docs"
        if docs_dir.exists():
            @app.get("/docs/{filename}")
            async def serve_docs(filename: str):
                if filename.endswith('.md'):
                    file_path = docs_dir / filename
                    if file_path.exists():
                        return FileResponse(str(file_path), media_type="text/markdown")
                raise HTTPException(status_code=404, detail="File not found")
        
        # Serve index.html for root and other non-API routes
        index_html = frontend_static_path / "index.html"
        if index_html.exists():
            logger.info(f"Frontend found at {index_html}, will serve SPA for root route")
            
            @app.get("/")
            async def serve_root():
                """Serve the frontend application."""
                return FileResponse(str(index_html))
            
            # Catch-all route to serve SPA for any unmatched routes (except API routes)
            @app.get("/{full_path:path}")
            async def serve_spa(full_path: str):
                """Serve the SPA for all unmatched routes."""
                # Skip API routes and static files - let them 404 naturally
                if (full_path.startswith("api/") or 
                    full_path.startswith("api-docs") or 
                    full_path.startswith("api-redoc") or
                    full_path.startswith("static/")):
                    raise HTTPException(status_code=404, detail="Not Found")
                return FileResponse(str(index_html))
        else:
            logger.warning(f"Frontend index.html not found at {index_html}")
            
            @app.get("/")
            async def redirect_to_docs():
                """Redirect to API documentation when frontend is not available."""
                if settings.DOCS_ENABLED:
                    return RedirectResponse(url="/api-docs")
                return {"message": "Kasal API", "version": settings.VERSION, "docs": "/api-docs"}
else:
    logger.info("FRONTEND_STATIC_DIR not set, frontend will not be served")
    
    @app.get("/")
    async def redirect_to_docs():
        """Redirect to API documentation when frontend is not available."""
        if settings.DOCS_ENABLED:
            return RedirectResponse(url="/api-docs")
        return {"message": "Kasal API", "version": settings.VERSION, "docs": "/api-docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG_MODE,
    )
