import requests
import json
from typing import Dict, Any
from enum import Enum
import time

class ScanType(str, Enum):
    ACTIVE = "active"
    PASSIVE = "passive"
    AJAX = "ajax"

class ReportFormat(str, Enum):
    HTML = "html"
    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"

class ZAPMCPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.headers = {}

    def check_zap_service(self) -> bool:
        """Check if ZAP service is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def login(self, username: str = "test", password: str = "test") -> str:
        """Get authentication token."""
        response = requests.post(
            f"{self.base_url}/api/v1/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        return self.token

    def start_scan(self, target_url: str, scan_type: ScanType = ScanType.ACTIVE) -> Dict[str, Any]:
        """Start a new security scan."""
        # First check if ZAP service is running
        if not self.check_zap_service():
            raise Exception("ZAP service is not running. Please start the ZAP service first.")

        # First, add the target to ZAP
        print("Adding target to ZAP...")
        response = requests.post(
            f"{self.base_url}/api/v1/scan/start",
            headers=self.headers,
            json={
                "target_url": target_url,
                "scan_type": scan_type.value,
                "scan_config": {
                    "max_depth": 5,
                    "max_children": 10,
                    "target_url": target_url
                },
                "report_format": ReportFormat.HTML.value,
                "timeout": 3600
            }
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success"):
            raise Exception(f"Failed to start scan: {result.get('error', 'Unknown error')}")
            
        if not result.get("payload", {}).get("scan_id"):
            raise Exception("No scan ID received from server")
            
        return result

    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get scan status."""
        response = requests.get(
            f"{self.base_url}/api/v1/scan/{scan_id}/status",
            headers=self.headers
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success"):
            raise Exception(f"Failed to get scan status: {result.get('error', 'Unknown error')}")
            
        return result

    def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        """Get scan results."""
        response = requests.get(
            f"{self.base_url}/api/v1/scan/{scan_id}/results",
            headers=self.headers
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success"):
            raise Exception(f"Failed to get scan results: {result.get('error', 'Unknown error')}")
            
        return result

    def generate_report(self, scan_id: str, format: ReportFormat = ReportFormat.HTML) -> Dict[str, Any]:
        """Generate a report."""
        response = requests.post(
            f"{self.base_url}/api/v1/reports/generate",
            headers=self.headers,
            json={
                "scan_id": scan_id,
                "format": format.value,
                "include_details": True,
                "report_path": f"reports/scan_{scan_id}.{format.value}"
            }
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success"):
            raise Exception(f"Failed to generate report: {result.get('error', 'Unknown error')}")
            
        return result

def create_claude_prompt(client: ZAPMCPClient, target_url: str) -> str:
    """Create a prompt for Claude AI to analyze security scan results."""
    try:
        # Check ZAP service first
        if not client.check_zap_service():
            raise Exception("ZAP service is not running. Please start the ZAP service first.")

        # Start a scan
        print(f"Starting scan for {target_url}...")
        scan_response = client.start_scan(target_url)
        scan_id = scan_response["payload"]["scan_id"]
        print(f"Scan started with ID: {scan_id}")
        
        # Poll for scan completion
        max_attempts = 60  # 5 minutes maximum
        attempt = 0
        while attempt < max_attempts:
            try:
                status_response = client.get_scan_status(scan_id)
                status = status_response["payload"]["status"]
                
                if status == "completed":
                    print("Scan completed successfully!")
                    break
                elif status == "failed":
                    raise Exception(f"Scan failed: {status_response.get('error', 'Unknown error')}")
                elif status == "does_not_exist":
                    raise Exception("Scan ID not found. ZAP service might have restarted.")
                
                print(f"Scan in progress... Status: {status}")
                time.sleep(5)  # Wait 5 seconds before next poll
                attempt += 1
            except requests.exceptions.RequestException as e:
                raise Exception(f"Error communicating with ZAP service: {str(e)}")
        
        if attempt >= max_attempts:
            raise Exception("Scan timed out after 5 minutes")
        
        # Get scan results
        print("Fetching scan results...")
        results = client.get_scan_results(scan_id)
        
        # Generate report
        print("Generating report...")
        report = client.generate_report(scan_id)
        
        # Create a prompt for Claude
        prompt = f"""Please analyze the following security scan results for {target_url}:

Scan ID: {scan_id}
Results: {json.dumps(results, indent=2)}
Report: {json.dumps(report, indent=2)}

Please provide:
1. A summary of the security findings
2. Risk assessment
3. Recommended actions
4. Any critical vulnerabilities that need immediate attention
"""
        return prompt
        
    except Exception as e:
        error_msg = f"Error during scan: {str(e)}"
        print(f"\nError: {error_msg}")
        return f"""Error occurred during security scan:

{error_msg}

Please check:
1. The target URL is accessible
2. The ZAP service is running (http://localhost:8000/health)
3. Your network connection
4. The server logs for more details
"""

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = ZAPMCPClient()
    
    # Check ZAP service first
    if not client.check_zap_service():
        print("Error: ZAP service is not running. Please start the ZAP service first.")
        print("You can start it with: python -m zap_mcp.server")
        exit(1)
    
    # Login
    token = client.login()
    print(f"Logged in successfully with token: {token[:20]}...")
    
    # Get target URL from user input
    target_url = input("Enter the target URL to scan: ")
    
    # Create prompt and display
    prompt = create_claude_prompt(client, target_url)
    print("\nGenerated Claude prompt:")
    print(prompt)
    print("\nYou can now copy this prompt and paste it into Claude Desktop for analysis.")