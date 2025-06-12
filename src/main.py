"""Main application module."""
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .bot.handlers import router as bot_router, handle_slack_event
from .auth.routes import router as auth_router
from .auth.propel_routes import router as propel_router
from .auth.protected_routes import router as protected_router
from .api.nl2sql_routes import router as nl2sql_router
from .api.ai_bot_routes import router as ai_bot_router
from .config import get_settings

app = FastAPI(
    title="your_company Slack Bot API",
    description="API for Slack bot with PropelAuth authentication",
    version="1.0.0",
    # Disable default docs endpoints - we'll create custom ones
    docs_url=None,
    redoc_url=None
)

# Add security scheme for bearer auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OpenAPI with security scheme
app.openapi_schema = {
    "openapi": "3.1.0",
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your PropelAuth JWT token"
            }
        }
    },
    "security": [{"bearerAuth": []}]
}

# Custom docs endpoint with auth
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Serve custom Swagger UI with bearer auth configuration."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

@app.on_event("startup")
async def startup_event():
    """Configure application on startup."""
    settings = get_settings()
    logger.info(f"Starting slack-bot in {settings.environment} environment")
    logger.info(f"Log level set to {settings.log_level}")
    
    # Log PropelAuth configuration
    logger.info("PropelAuth configuration:")
    logger.info(f"PropelAuth URL: {settings.propelauth_url}")
    logger.info("PropelAuth API key is configured" if settings.propelauth_api_key else "PropelAuth API key is missing")

# Add root path handler for health checks
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy"}

# Add a simple hello endpoint
@app.get("/hello")
async def hello():
    """Simple hello endpoint."""
    return {"message": "Hello, World!"}

# Add error handler for root POST requests
@app.post("/")
async def handle_root_post(request: Request):
    """Handle POST requests to root path."""
    try:
        body = await request.json()
        logger.info(f"ROOT POST received with body: {body}")
        
        # Handle URL verification directly here
        if "type" in body and body.get("type") == "url_verification":
            logger.info(f"Handling URL verification in root handler")
            challenge = body.get("challenge")
            if challenge:
                logger.info(f"Returning challenge: {challenge}")
                # Return challenge in the format Slack expects
                return {"challenge": challenge}
        
        # For other Slack events, forward to the events handler
        if "type" in body and body.get("type") == "event_callback":
            logger.info(f"Forwarding event_callback to events handler")
            return await handle_slack_event(request)
            
    except Exception as e:
        logger.error(f"Error handling root POST: {str(e)}")
        
    return JSONResponse(status_code=404, content={"error": "Not found"})

# Mount routers
app.include_router(auth_router, prefix="/auth")
app.include_router(propel_router, prefix="/auth")  # Mount PropelAuth routes under /auth
app.include_router(protected_router, prefix="/api")
app.include_router(nl2sql_router, prefix="/api")  # Mount NL2SQL routes under /api
app.include_router(ai_bot_router, prefix="/api")  # Mount AI bot routes under /api
app.include_router(bot_router, prefix="/slack")

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# Add a health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.development_mode
    ) 