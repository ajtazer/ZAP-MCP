from typing import Dict, Any
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..core.auth import (
    get_current_user,
    create_access_token,
    Token,
    User
)
from ..core.config import Settings, get_settings
from ..models.mcp import (
    MCPMessage,
    MCPResponse,
    ScanRequest,
    ScanResult,
    ConfigRequest,
    ReportRequest
)
from ..services.zap_service import ZAPService

router = APIRouter()

@router.get("/")
async def api_root():
    """Root API endpoint."""
    return {
        "name": "ZAP-MCP API",
        "version": "1.0.0",
        "endpoints": {
            "token": "/token",
            "scan": {
                "start": "/scan/start",
                "status": "/scan/{scan_id}/status",
                "results": "/scan/{scan_id}/results"
            },
            "config": "/config",
            "reports": "/reports/generate"
        }
    }

# Dependency to get ZAP service
async def get_zap_service(settings: Settings = Depends(get_settings)) -> ZAPService:
    return ZAPService(settings.zap_api_url, settings.zap_api_key)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings)
):
    """Login endpoint to get access token."""
    # Here you would typically validate against your user database
    # For now, we'll use a mock user
    if form_data.username != "test" or form_data.password != "test":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": form_data.username},
        settings=settings,
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/scan/start", response_model=MCPResponse)
async def start_scan(
    request: ScanRequest,
    current_user: User = Depends(get_current_user),
    zap_service: ZAPService = Depends(get_zap_service)
):
    """Start a new security scan."""
    try:
        scan_result = await zap_service.start_scan(
            target_url=request.target_url,
            scan_type=request.scan_type,
            scan_config=request.scan_config
        )
        return MCPResponse(
            success=True,
            payload={"scan_id": scan_result["scan_id"]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/scan/{scan_id}/status", response_model=MCPResponse)
async def get_scan_status(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    zap_service: ZAPService = Depends(get_zap_service)
):
    """Get the status of a running scan."""
    try:
        status = await zap_service.get_scan_status(scan_id)
        return MCPResponse(success=True, payload=status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/scan/{scan_id}/results", response_model=MCPResponse)
async def get_scan_results(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    zap_service: ZAPService = Depends(get_zap_service)
):
    """Get the results of a completed scan."""
    try:
        results = await zap_service.get_scan_results(scan_id)
        return MCPResponse(success=True, payload=results)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/config", response_model=MCPResponse)
async def update_config(
    request: ConfigRequest,
    current_user: User = Depends(get_current_user),
    zap_service: ZAPService = Depends(get_zap_service)
):
    """Update ZAP configuration."""
    try:
        result = await zap_service.update_config(request.config)
        return MCPResponse(success=True, payload=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/reports/generate", response_model=MCPResponse)
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_user),
    zap_service: ZAPService = Depends(get_zap_service)
):
    """Generate a security report."""
    try:
        report = await zap_service.generate_report(
            scan_id=request.scan_id,
            report_format=request.format,
            report_path=request.report_path
        )
        return MCPResponse(success=True, payload=report)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 