#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for ZAP-MCP integration.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from zapv2 import ZAPv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPConfig(BaseModel):
    host: str = "localhost"
    port: int = 7456
    model: str = "claude-instant-v1"
    max_tokens: int = 1000
    temperature: float = 0.7
    zap_api_key: Optional[str] = None
    zap_url: str = "http://localhost:8080"

class ZAPTools:
    def __init__(self, config: MCPConfig):
        self.config = config
        self.zap = ZAPv2(apikey=config.zap_api_key, proxies={'http': config.zap_url, 'https': config.zap_url})

    async def start_scan(self, target_url: str) -> Dict[str, Any]:
        """Start a new ZAP scan."""
        try:
            scan_id = self.zap.spider.scan(target_url)
            return {"status": "success", "scan_id": scan_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get the status of a running scan."""
        try:
            status = self.zap.spider.status(scan_id)
            return {"status": "success", "scan_status": status}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_alerts(self) -> Dict[str, Any]:
        """Get all alerts from the current scan."""
        try:
            alerts = self.zap.core.alerts()
            return {"status": "success", "alerts": alerts}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_scan_summary(self) -> Dict[str, Any]:
        """Get a summary of the current scan."""
        try:
            summary = {
                "hosts": self.zap.core.hosts,
                "sites": self.zap.core.sites,
                "urls": self.zap.core.urls,
                "alerts": self.zap.core.alerts
            }
            return {"status": "success", "summary": summary}
        except Exception as e:
            return {"status": "error", "error": str(e)}

class MCPServer:
    def __init__(self, config_path: str, model_dir: str):
        self.config_path = config_path
        self.model_dir = model_dir
        self.config = self._load_config()
        self.app = FastAPI()
        self.zap_tools = ZAPTools(self.config)
        self.setup_routes()

    def _load_config(self) -> MCPConfig:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                return MCPConfig(**config_data.get('mcp_server', {}))
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            sys.exit(1)

    def setup_routes(self):
        """Setup FastAPI routes."""
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_text()
                    logger.info(f"Received: {data}")
                    
                    # Process the request
                    response = await self.process_request(data)
                    
                    # Send response back to client
                    await websocket.send_text(json.dumps(response))
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await websocket.close()

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "config": self.config.dict()}

    async def process_request(self, data: str) -> Dict[str, Any]:
        """Process incoming requests."""
        try:
            request = json.loads(data)
            action = request.get('action')
            params = request.get('params', {})

            if action == 'start_scan':
                return await self.zap_tools.start_scan(params.get('target_url'))
            elif action == 'get_scan_status':
                return await self.zap_tools.get_scan_status(params.get('scan_id'))
            elif action == 'get_alerts':
                return await self.zap_tools.get_alerts()
            elif action == 'get_scan_summary':
                return await self.zap_tools.get_scan_summary()
            else:
                return {
                    "status": "error",
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def start(self):
        """Start the MCP server."""
        import uvicorn
        logger.info(f"Starting MCP server with config: {self.config.dict()}")
        logger.info(f"Model directory: {self.model_dir}")
        
        config = uvicorn.Config(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

def main():
    parser = argparse.ArgumentParser(description='MCP Server for ZAP-MCP')
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--model-dir', required=True, help='Path to model directory')
    args = parser.parse_args()

    server = MCPServer(args.config, args.model_dir)
    asyncio.run(server.start())

if __name__ == '__main__':
    main() 