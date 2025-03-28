import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import os

from zap_mcp.api.routes import router as api_router
from zap_mcp.core.auth import get_current_user
from zap_mcp.core.config import Settings, get_settings
from zap_mcp.core.mcp import MCPHandler
from zap_mcp.services.zap_service import ZAPService
from zap_mcp.services.claude_service import ClaudeScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZAP-MCP Server",
    description="Model Context Protocol Server for OWASP ZAP Integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory="zap_mcp/templates")

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Global MCP handler instance
mcp_handler: Optional[MCPHandler] = None
zap_service: Optional[ZAPService] = None
claude_scanner: Optional[ClaudeScanner] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global mcp_handler, zap_service, claude_scanner
    try:
        settings = get_settings()
        
        # Initialize ZAP service
        zap_service = ZAPService(settings.zap_api_url, settings.zap_api_key)
        
        # Initialize Claude scanner
        claude_scanner = ClaudeScanner(settings)
        
        # Initialize MCP handler
        mcp_handler = MCPHandler(zap_service, claude_scanner)
        
        # Start MCP handler
        await mcp_handler.start()
        logger.info("MCP handler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP handler: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if mcp_handler:
        await mcp_handler.stop()
    if zap_service:
        await zap_service.close()
    if claude_scanner:
        await claude_scanner.close()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint with HTML interface."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "version": "1.0.0",
            "status": "running"
        }
    )

@app.get("/events")
async def events(
    settings: Settings = Depends(get_settings)
):
    """SSE endpoint for real-time updates."""
    if not mcp_handler:
        raise HTTPException(status_code=503, detail="MCP handler not initialized")
    
    return EventSourceResponse(mcp_handler.event_stream())

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mcp_handler": mcp_handler is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 