import uvicorn
from zap_mcp.server import app

if __name__ == "__main__":
    uvicorn.run(
        "zap_mcp.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 