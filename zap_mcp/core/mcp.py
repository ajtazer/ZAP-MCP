import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

from ..services.zap_service import ZAPService
from ..services.claude_service import ClaudeScanner
from ..models.mcp import MCPMessage, MCPResponse, ScanRequest, ScanResult

logger = logging.getLogger(__name__)

class MCPHandler:
    def __init__(self, zap_service: ZAPService, claude_scanner: ClaudeScanner):
        self.zap_service = zap_service
        self.claude_scanner = claude_scanner
        self.message_queue = asyncio.Queue()
        self.active_scans: Dict[str, asyncio.Task] = {}
        self._running = False

    async def start(self):
        """Start the MCP handler."""
        self._running = True
        asyncio.create_task(self._process_messages())

    async def stop(self):
        """Stop the MCP handler and cleanup."""
        self._running = False
        # Cancel all active scans
        for scan_id, task in self.active_scans.items():
            task.cancel()
        self.active_scans.clear()
        await self.claude_scanner.close()

    async def handle_message(self, message: MCPMessage) -> MCPResponse:
        """Handle incoming MCP messages."""
        try:
            if message.type == "scan_request":
                return await self._handle_scan_request(message)
            elif message.type == "config_request":
                return await self._handle_config_request(message)
            elif message.type == "report_request":
                return await self._handle_report_request(message)
            else:
                return MCPResponse(
                    success=False,
                    error=f"Unknown message type: {message.type}"
                )
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return MCPResponse(success=False, error=str(e))

    async def _handle_scan_request(self, message: MCPMessage) -> MCPResponse:
        """Handle scan requests."""
        scan_request = ScanRequest(**message.payload)
        
        # Create a new scan task
        scan_id = f"scan_{datetime.now().timestamp()}"
        scan_task = asyncio.create_task(
            self._run_scan(scan_id, scan_request)
        )
        
        self.active_scans[scan_id] = scan_task
        
        return MCPResponse(
            success=True,
            payload={"scan_id": scan_id}
        )

    async def _run_scan(self, scan_id: str, request: ScanRequest):
        """Run a security scan with the given parameters."""
        try:
            # Start parallel scans
            zap_task = asyncio.create_task(
                self.zap_service.start_scan(
                    target_url=request.target_url,
                    scan_type=request.scan_type,
                    scan_config=request.scan_config
                )
            )
            
            claude_task = asyncio.create_task(
                self.claude_scanner.scan_code(request)
            )
            
            # Wait for both scans to complete
            zap_results, claude_results = await asyncio.gather(zap_task, claude_task)
            
            # Combine results
            combined_results = {
                "scan_id": scan_id,
                "zap_results": zap_results,
                "claude_results": claude_results,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send results through event stream
            await self.message_queue.put({
                "type": "scan_complete",
                "scan_id": scan_id,
                "results": combined_results
            })
            
        except Exception as e:
            logger.error(f"Error running scan {scan_id}: {str(e)}")
            await self.message_queue.put({
                "type": "scan_error",
                "scan_id": scan_id,
                "error": str(e)
            })
        finally:
            if scan_id in self.active_scans:
                del self.active_scans[scan_id]

    async def _handle_config_request(self, message: MCPMessage) -> MCPResponse:
        """Handle configuration requests."""
        config = message.payload
        await self.zap_service.update_config(config)
        return MCPResponse(success=True)

    async def _handle_report_request(self, message: MCPMessage) -> MCPResponse:
        """Handle report generation requests."""
        report_params = message.payload
        report = await self.zap_service.generate_report(**report_params)
        return MCPResponse(success=True, payload={"report": report})

    async def _process_messages(self):
        """Process messages from the queue."""
        while self._running:
            try:
                message = await self.message_queue.get()
                await self.handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")

    async def event_stream(self) -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        while self._running:
            try:
                event = await self.message_queue.get()
                yield json.dumps(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event stream: {str(e)}")
                await asyncio.sleep(1) 