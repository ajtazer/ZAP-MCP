from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Server configuration settings."""
    # Server settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # ZAP settings
    zap_api_url: str = os.getenv("ZAP_API_URL", "http://127.0.0.1:8080")
    zap_api_key: str = os.getenv("ZAP_API_KEY", "m6d1i03ertsikiuf8kkudjlsap")
    
    # Security settings
    secret_key: str = os.getenv("SECRET_KEY", "ktki")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # MCP settings
    mcp_version: str = os.getenv("MCP_VERSION", "1.0")
    max_concurrent_scans: int = int(os.getenv("MAX_CONCURRENT_SCANS", "5"))
    scan_timeout: int = int(os.getenv("SCAN_TIMEOUT", "3600"))  # 1 hour
    
    # Report settings
    report_dir: str = os.getenv("REPORT_DIR", "reports")
    default_report_format: str = os.getenv("DEFAULT_REPORT_FORMAT", "html")
    
    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.getenv("LOG_FILE")

    # Claude settings
    claude_config: Dict[str, Any] = Field(default_factory=lambda: {
        "mcp_server": {
            "host": os.getenv("MCP_HOST", "localhost"),
            "port": int(os.getenv("MCP_PORT", "7456")),
            "model": os.getenv("MCP_MODEL", "claude-instant-v1"),
            "max_tokens": int(os.getenv("MCP_MAX_TOKENS", "1000")),
            "temperature": float(os.getenv("MCP_TEMPERATURE", "0.7")),
            "api_key": os.getenv("CLAUDE_API_KEY", "")
        },
        "local_models": {
            "path": os.getenv("LOCAL_MODELS_PATH", "./models"),
            "prefer_local": os.getenv("PREFER_LOCAL_MODELS", "true").lower() == "true"
        }
    })

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 