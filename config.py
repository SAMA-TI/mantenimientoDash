"""
Configuration file for Mantenimiento Dashboard
All configurable variables are centralized here for easy management and Docker deployment

This config now reads from the central .env.sama-dashboards file if available,
or falls back to local .env or environment variables.
"""

import os
from pathlib import Path

# Try to load central .env file
def load_central_env():
    """Load environment variables from central .env.sama-dashboards file"""
    central_env = Path.home() / ".env.sama-dashboards"
    if central_env.exists():
        try:
            with open(central_env) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load {central_env}: {e}")

# Load central configuration
load_central_env()

# ====================
# APPLICATION SETTINGS
# ====================

# Server Configuration
# Try MANTENIMIENTO_* variables first (from central .env), then fall back to APP_* variables
APP_HOST = os.getenv("MANTENIMIENTO_HOST", os.getenv("APP_HOST", "0.0.0.0"))
APP_PORT = int(os.getenv("MANTENIMIENTO_PORT", os.getenv("APP_PORT", "8000")))
DEBUG_MODE = os.getenv("MANTENIMIENTO_DEBUG", os.getenv("DEBUG_MODE", "False")).lower() == "true"

# ====================
# DATA SETTINGS
# ====================

# Data Directory
DATA_FOLDER = os.getenv("MANTENIMIENTO_DATA_FOLDER", os.getenv("DATA_FOLDER", "./Analisis6"))

# Database Configuration (if needed in the future)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "mantenimiento")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ====================
# API SETTINGS
# ====================

# External API Configuration (if needed)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))

# ====================
# ANALYSIS SETTINGS
# ====================

# Data processing settings
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"

# ====================
# LOGGING SETTINGS
# ====================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "app.log")

# ====================
# DISPLAY CONFIGURATION
# ====================

def get_config_info():
    """Return a formatted string with current configuration"""
    return f"""
    {'='*60}
    🚀 Iniciando servidor Dash...
    📍 Host: {APP_HOST}
    📍 Port: {APP_PORT}
    📍 Debug Mode: {DEBUG_MODE}
    📂 Data Folder: {DATA_FOLDER}
    {'='*60}
    """
