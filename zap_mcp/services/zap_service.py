import logging
from typing import Dict, Any, Optional
import aiohttp
from zapv2 import ZAPv2

logger = logging.getLogger(__name__)

class ZAPService:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.zap = ZAPv2(apikey=api_key, proxies={'http': api_url, 'https': api_url})
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def close(self):
        """Close the service and cleanup resources."""
        if self._session:
            await self._session.close()

    async def start_scan(
        self,
        target_url: str,
        scan_type: str = "active",
        scan_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a new security scan."""
        try:
            # Configure scan parameters
            scan_config = scan_config or {}
            
            # Start the scan based on type
            if scan_type == "active":
                scan_id = self.zap.ascan.scan(target_url, scan_config)
            elif scan_type == "passive":
                scan_id = self.zap.pscan.scan(target_url, scan_config)
            else:
                raise ValueError(f"Unsupported scan type: {scan_type}")
            
            return {
                "scan_id": scan_id,
                "status": "started",
                "target_url": target_url
            }
            
        except Exception as e:
            logger.error(f"Error starting scan: {str(e)}")
            raise

    async def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get the status of a running scan."""
        try:
            # Get scan status from ZAP
            status = self.zap.ascan.status(scan_id)
            
            return {
                "scan_id": scan_id,
                "status": status,
                "progress": self.zap.ascan.scan_progress(scan_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting scan status: {str(e)}")
            raise

    async def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        """Get the results of a completed scan."""
        try:
            # Get alerts from ZAP
            alerts = self.zap.core.alerts()
            
            # Get scan results
            results = {
                "scan_id": scan_id,
                "alerts": alerts,
                "risk_levels": self._calculate_risk_levels(alerts),
                "summary": self._generate_summary(alerts)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting scan results: {str(e)}")
            raise

    async def generate_report(
        self,
        scan_id: str,
        report_format: str = "html",
        report_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a security report."""
        try:
            # Generate report based on format
            if report_format == "html":
                report = self.zap.reports.generate(
                    title="Security Scan Report",
                    template="traditional-html",
                    reportfilename=f"scan_{scan_id}.html",
                    reportdir=report_path or "reports"
                )
            elif report_format == "json":
                report = self.zap.reports.generate(
                    title="Security Scan Report",
                    template="traditional-json",
                    reportfilename=f"scan_{scan_id}.json",
                    reportdir=report_path or "reports"
                )
            else:
                raise ValueError(f"Unsupported report format: {report_format}")
            
            return {
                "scan_id": scan_id,
                "report_path": report,
                "format": report_format
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise

    async def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update ZAP configuration."""
        try:
            # Update ZAP configuration
            for key, value in config.items():
                self.zap.core.set_option(key, value)
            
            return {
                "status": "success",
                "message": "Configuration updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
            raise

    def _calculate_risk_levels(self, alerts: list) -> Dict[str, int]:
        """Calculate risk level statistics from alerts."""
        risk_levels = {
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for alert in alerts:
            risk = alert.get("risk", "").lower()
            if risk in risk_levels:
                risk_levels[risk] += 1
        
        return risk_levels

    def _generate_summary(self, alerts: list) -> Dict[str, Any]:
        """Generate a summary of the scan results."""
        summary = {
            "total_alerts": len(alerts),
            "unique_issues": len(set(alert["name"] for alert in alerts)),
            "risk_distribution": self._calculate_risk_levels(alerts),
            "top_vulnerabilities": self._get_top_vulnerabilities(alerts)
        }
        
        return summary

    def _get_top_vulnerabilities(self, alerts: list, limit: int = 5) -> list:
        """Get the top vulnerabilities by risk level."""
        # Sort alerts by risk level (high > medium > low > info)
        risk_levels = {"high": 3, "medium": 2, "low": 1, "info": 0}
        sorted_alerts = sorted(
            alerts,
            key=lambda x: risk_levels.get(x.get("risk", "").lower(), -1),
            reverse=True
        )
        
        return sorted_alerts[:limit] 