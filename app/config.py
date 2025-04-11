"""
Configuration module for the application.
Loads and validates environment variables.
"""
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
from secrets import token_hex


class Settings(BaseSettings):
    """
    Application settings class that loads and validates environment variables.
    """
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ServiceMesh API"
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", token_hex(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:6000"]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/monitoring")
    DATABASE_CONNECT_ARGS: Dict[str, Any] = {}
    DATABASE_MIGRATION: bool = os.getenv("DATABASE_MIGRATION", "false").lower() == "true"
    
    # Uptime Kuma
    UPTIME_KUMA_URL: str = os.getenv("UPTIME_KUMA_URL", "")
    UPTIME_KUMA_USERNAME: str = os.getenv("UPTIME_KUMA_USERNAME", "")
    UPTIME_KUMA_PASSWORD: str = os.getenv("UPTIME_KUMA_PASSWORD", "")
    
    # Prometheus
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "")
    PROMETHEUS_USERNAME: Optional[str] = os.getenv("PROMETHEUS_USERNAME", "")
    PROMETHEUS_PASSWORD: Optional[str] = os.getenv("PROMETHEUS_PASSWORD", "")
    
    # Grafana
    GRAFANA_URL: str = os.getenv("GRAFANA_URL", "")
    GRAFANA_API_KEY: str = os.getenv("GRAFANA_API_KEY", "")
    GRAFANA_USERNAME: str = os.getenv("GRAFANA_USERNAME", "")
    GRAFANA_PASSWORD: str = os.getenv("GRAFANA_PASSWORD", "")
    
    # Proxmox
    PROXMOX_URL: str = os.getenv("PROXMOX_URL", "")
    PROXMOX_USERNAME: str = os.getenv("PROXMOX_USERNAME", "")
    PROXMOX_PASSWORD: str = os.getenv("PROXMOX_PASSWORD", "")
    PROXMOX_VERIFY_SSL: bool = os.getenv("PROXMOX_VERIFY_SSL", "True").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Timeouts (in seconds)
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "10"))
    
    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Validate CORS origins.
        
        Args:
            v: CORS origins as string or list
            
        Returns:
            List of validated CORS origins
        """
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # Handle JSON-formatted string list
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated string
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5000"]  # Default value if parsing fails

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()
