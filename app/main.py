"""
Entry point for the FastAPI application.
This module initializes and configures the API.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.api.router import main_router
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.api.endpoints import credentials
from app.config import get_settings

# Configure logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle startup and shutdown events.
    """
    from app.config import get_settings
    from app.database.base import Base
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.database.models import User, ServiceCredentials
    
    logger.info("Starting up monitoring and infrastructure management API")
    
    # Initialize database if needed
    settings = get_settings()
    if settings.DATABASE_MIGRATION:
        try:
            # Create async engine and session
            db_url = settings.DATABASE_URL
            logger.info(f"Initializing database: {db_url}")
            
            engine = create_async_engine(
                db_url, 
                pool_pre_ping=True,
                **settings.DATABASE_CONNECT_ARGS
            )
            
            async with engine.begin() as conn:
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                
                # Check if admin user exists
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM users WHERE is_superuser = TRUE")
                )
                admin_exists = result.scalar() > 0
                
                if not admin_exists:
                    logger.info("Creating default admin user...")
                    # Create default admin user
                    admin_password = settings.ADMIN_DEFAULT_PASSWORD
                    hashed_password = pwd_context.hash(admin_password)
                    
                    await conn.execute(
                        text("""
                            INSERT INTO users (username, email, hashed_password, 
                            is_active, is_superuser, created_at, updated_at)
                            VALUES (:username, :email, :password, TRUE, TRUE, 
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """),
                        {
                            "username": "admin",
                            "email": "admin@localhost",
                            "password": hashed_password
                        }
                    )
                    logger.info("Default admin user created successfully!")
            
        except Exception as e:
            logger.error(f"Error during database initialization: {e}")
            # Continue startup even if database initialization fails
    
    yield
    
    # Perform cleanup operations here, such as closing connections
    logger.info("Shutting down monitoring and infrastructure management API")


# Initialize FastAPI application with custom configuration
app = FastAPI(
    title="ServiceMesh API",
    description="A high-performance API for infrastructure monitoring and management",
    version="1.0.0",  # Change this to your desired version
    openapi_url="/openapi.json",
    lifespan=lifespan,
    docs_url=None,  # We'll serve custom Swagger UI
    redoc_url=None,  # We'll serve custom ReDoc
)

# Configure CORS
origins = os.environ.get("CORS_ORIGINS", "http://localhost:5000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Include API router
app.include_router(main_router)


from fastapi.responses import HTMLResponse, FileResponse
import os.path

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Serve custom Swagger UI with dark theme from static file."""
    swagger_ui_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "app", "templates", "html", "swagger_doc.html"
    )
    return FileResponse(swagger_ui_path)

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    """Serve OpenAPI schema."""
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=6000,
        log_level="info",
        reload=bool(os.environ.get("DEBUG", "False").lower() == "true"),
    )

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="app/templates/static"), name="static")
