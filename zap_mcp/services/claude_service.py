import os
import json
import httpx
import websockets
from typing import Dict, Any, Optional
from fastapi import Depends
from ..core.config import Settings, get_settings
from ..models.mcp import ScanRequest, ScanResult, Vulnerability

class MCPClient:
    def __init__(self, settings: Settings):
        self.cfg = settings.claude_config
        self.uri = f"ws://{self.cfg['mcp_server']['host']}:{self.cfg['mcp_server']['port']}/ws"
        self.use_local = self.cfg['local_models']['prefer_local']

    async def analyze(self, prompt: str) -> dict:
        if self.use_local:
            return await self._analyze_local(prompt)
        return await self._analyze_remote(prompt)

    async def _analyze_local(self, prompt: str) -> dict:
        async with websockets.connect(self.uri) as websocket:
            payload = {
                "prompt": prompt,
                "model": self.cfg['mcp_server']['model'],
                "max_tokens": self.cfg['mcp_server']['max_tokens'],
                "temperature": self.cfg['mcp_server']['temperature']
            }
            await websocket.send(json.dumps(payload))
            response = await websocket.recv()
            return json.loads(response)

    async def _analyze_remote(self, prompt: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.cfg['api_key'],
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.cfg['mcp_server']['model'],
                    "max_tokens": self.cfg['mcp_server']['max_tokens'],
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }],
                    "temperature": self.cfg['mcp_server']['temperature']
                }
            )
            response.raise_for_status()
            return response.json()

class ClaudeScanner:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.client = MCPClient(settings)

    async def scan_code(self, request: ScanRequest) -> ScanResult:
        """Perform LLM-based code analysis using Claude."""
        try:
            prompt = self._build_analysis_prompt(request.content)
            response = await self.client.analyze(prompt)
            return self._parse_response(response)
        except Exception as e:
            raise Exception(f"Claude analysis failed: {str(e)}")

    def _build_analysis_prompt(self, code: str) -> str:
        """Build the analysis prompt for Claude."""
        return f"""Analyze this code for security vulnerabilities:

{code}

Provide findings in JSON format with the following structure:
{{
    "vulnerabilities": [
        {{
            "name": "Vulnerability name",
            "risk": "High/Medium/Low",
            "description": "Detailed description",
            "solution": "Suggested fix",
            "references": ["Reference links"],
            "instances": [
                {{
                    "file": "filename",
                    "line": "line number",
                    "code": "vulnerable code snippet"
                }}
            ],
            "cwe_id": "CWE identifier",
            "cvss_score": "CVSS score"
        }}
    ],
    "summary": {{
        "total_vulnerabilities": "number",
        "risk_distribution": {{
            "high": "count",
            "medium": "count",
            "low": "count"
        }},
        "top_issues": ["list of top issues"]
    }}
}}

Focus on:
1. Security vulnerabilities
2. Code quality issues
3. Best practices violations
4. Potential backdoors
5. Authentication/Authorization issues
6. Data validation problems
7. Cryptographic issues
8. Configuration problems
"""

    def _parse_response(self, response: str) -> ScanResult:
        """Parse Claude's response into a ScanResult."""
        try:
            data = json.loads(response)
            vulnerabilities = [
                Vulnerability(**vuln) for vuln in data.get("vulnerabilities", [])
            ]
            
            return ScanResult(
                scan_id=f"claude_{os.urandom(4).hex()}",
                status="completed",
                alerts=vulnerabilities,
                risk_levels=data.get("summary", {}).get("risk_distribution", {}),
                summary=data.get("summary", {})
            )
        except json.JSONDecodeError:
            raise Exception("Failed to parse Claude response as JSON")
        except Exception as e:
            raise Exception(f"Failed to create ScanResult: {str(e)}")

    async def close(self):
        """Cleanup resources."""
        pass  # No cleanup needed for WebSocket client 