# ============ APPLICATION CONFIGURATION MANAGEMENT ============
# This module loads and manages application settings from environment variables.
# 
# Purpose:
#   - Centralize all configuration in one place
#   - Load sensitive data (.env file) instead of hardcoding
#   - Support different configurations for dev/staging/production
#   - Type-validate settings (Pydantic ensures correct types)
#
# Security Note:
#   - NEVER commit .env file to version control (add to .gitignore)
#   - Keep SECRET_KEY random and long (32+ characters)
#   - Use environment variables in production (container secrets, CI/CD platforms)

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    FastAPI Application Settings
    
    All fields are loaded from the .env file or environment variables.
    If a setting is missing, application startup will fail with a validation error.
    """
    
    # ========== DATABASE CONNECTION SETTINGS ==========
    database_hostname: str              # PostgreSQL server address (localhost, IP, or domain)
    database_port: int                  # PostgreSQL port (default 5432)
    database_username: str              # PostgreSQL user account
    database_password: str              # PostgreSQL password (SECURITY: Use .env, never hardcode)
    database_name: str                  # Database name to connect to
    database_driver: str                # Database driver (e.g., "postgresql" for psycopg2 adapter)
    
    # ========== JWT AUTHENTICATION SETTINGS ==========
    secret_key: str                     # Secret key for signing JWT tokens
                                        # SECURITY: Must be random and kept secret
                                        # Generate with: openssl rand -hex 32
    algorithm: str                      # JWT signing algorithm (e.g., "HS256")
                                        # Options: HS256 (symmetric), RS256 (asymmetric)
    access_token_expire_minutes: int    # JWT token expiration time in minutes
                                        # Typical: 30 min (short, balances security vs UX)
    
    class Config:
        """Pydantic configuration for Settings class"""
        env_file = "app/.env"           # Load settings from .env file (relative to project root)
        # If env_file doesn't exist, Pydantic will still look for environment variables
  
# ========== SETTINGS SINGLETON ==========
# Create a single Settings instance used throughout the application
# FastAPI loads this once at startup
settings = Settings()