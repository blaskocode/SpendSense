"""FastAPI application main module"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ..utils.logger import setup_logger
from . import user_routes, data_routes, operator_routes, eval_routes

logger = setup_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="SpendSense API",
        description="Intelligent Behavioral Spending Trainer API",
        version="1.0.0"
    )
    
    # CORS middleware for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(user_routes.router)
    app.include_router(data_routes.router)
    app.include_router(operator_routes.router)
    app.include_router(eval_routes.router)
    
    # Serve static files (web UI)
    try:
        from pathlib import Path
        static_dir = Path(__file__).parent.parent.parent / "web" / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
            logger.info(f"Static files mounted from: {static_dir}")
            
            # Serve index.html at root
            @app.get("/", include_in_schema=False)
            def read_root():
                from fastapi.responses import FileResponse
                index_file = static_dir / "index.html"
                if index_file.exists():
                    return FileResponse(index_file)
                return {"service": "SpendSense API", "version": "1.0.0", "status": "running"}
            
            # Serve operator dashboard
            @app.get("/operator-dashboard", include_in_schema=False)
            def read_operator_dashboard():
                from fastapi.responses import FileResponse
                operator_file = static_dir / "operator.html"
                if operator_file.exists():
                    return FileResponse(operator_file)
                return {"error": "Operator dashboard not found"}
        else:
            logger.warning(f"Static directory not found: {static_dir}")
            # If static files don't exist, provide JSON API info at root
            @app.get("/")
            def root():
                """Root endpoint"""
                return {
                    "service": "SpendSense API",
                    "version": "1.0.0",
                    "status": "running",
                    "endpoints": {
                        "user_management": "/users",
                        "data_analysis": "/data",
                        "operator": "/operator",
                        "evaluation": "/eval",
                        "docs": "/docs"
                    }
                }
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
        # Fallback JSON endpoint if static files fail
        @app.get("/")
        def root():
            """Root endpoint"""
            return {
                "service": "SpendSense API",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "user_management": "/users",
                    "data_analysis": "/data",
                    "operator": "/operator",
                    "evaluation": "/eval",
                    "docs": "/docs"
                }
            }
    
    # API info endpoint (always available)
    @app.get("/api/info", include_in_schema=True)
    def api_info():
        """API information endpoint"""
        return {
            "service": "SpendSense API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "user_management": "/users",
                "data_analysis": "/data",
                "operator": "/operator",
                "evaluation": "/eval",
                "docs": "/docs",
                "user_dashboard": "/",
                "operator_dashboard": "/operator-dashboard"
            }
        }
    
    @app.get("/health")
    def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)}
        )
    
    logger.info("SpendSense API application created")
    
    return app

