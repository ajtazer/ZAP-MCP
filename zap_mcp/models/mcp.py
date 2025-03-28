from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class ScanType(str, Enum):
    ACTIVE = "active"
    PASSIVE = "passive"
    AJAX = "ajax"

class ReportFormat(str, Enum):
    HTML = "html"
    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"

class MCPMessage(BaseModel):
    """Base MCP message model."""
    type: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    """Base MCP response model."""
    success: bool
    payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ScanRequest(BaseModel):
    """Security scan request model."""
    target_url: str
    scan_type: ScanType = ScanType.ACTIVE
    scan_config: Optional[Dict[str, Any]] = None
    report_format: ReportFormat = ReportFormat.HTML
    timeout: Optional[int] = 3600  # Default 1 hour timeout

class ScanResult(BaseModel):
    """Security scan result model."""
    scan_id: str
    status: str
    alerts: List[Dict[str, Any]]
    risk_levels: Dict[str, int]
    summary: Dict[str, Any]
    report_path: Optional[str] = None

class ConfigRequest(BaseModel):
    """ZAP configuration request model."""
    config: Dict[str, Any]
    scope: Optional[str] = "global"  # global, scan, or session

class ReportRequest(BaseModel):
    """Report generation request model."""
    scan_id: str
    format: ReportFormat
    include_details: bool = True
    report_path: Optional[str] = None

class Vulnerability(BaseModel):
    """Vulnerability model."""
    name: str
    risk: str
    description: str
    solution: str
    references: List[str]
    instances: List[Dict[str, Any]]
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None

class ScanSummary(BaseModel):
    """Scan summary model."""
    total_alerts: int
    unique_issues: int
    risk_distribution: Dict[str, int]
    top_vulnerabilities: List[Dict[str, Any]]
    scan_duration: Optional[float] = None
    target_url: str
    scan_type: ScanType 