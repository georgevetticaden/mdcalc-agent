"""
Configuration management for MDCalc MCP Server.
Uses Pydantic Settings for environment variable loading.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Environment configuration for MDCalc MCP Server.

    Required Environment Variables:
    - AUTH0_DOMAIN: Your Auth0 tenant domain (e.g., dev-xyz.us.auth0.com)
    - AUTH0_ISSUER: Your Auth0 issuer URL with trailing slash
    - AUTH0_API_AUDIENCE: API audience identifier (matches MCP_SERVER_URL)
    - MCP_SERVER_URL: Public URL of this MCP server
    - PORT: Server port (default: 8080)
    """

    AUTH0_DOMAIN: str
    AUTH0_ISSUER: str
    AUTH0_API_AUDIENCE: str
    MCP_SERVER_URL: str
    PORT: int = 8080

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
