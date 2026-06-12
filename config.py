"""
EvaMusic — Configuration File
Handles API endpoints, MongoDB connection, and app settings.
"""

import os
from urllib.parse import urlencode


# ═══════════════════════════════════════════════════════════════
# Koyeb App 1 — Website (EvaMusic Frontend)
# ═══════════════════════════════════════════════════════════════
WEB_BASE_URL = os.environ.get(
    "WEB_BASE_URL",
    "http://your-evamusicwebsite.koyeb.app"   # ← replace with your website FQDN
).rstrip("/")


# ═══════════════════════════════════════════════════════════════
# Koyeb App 2 — API (JioSaavn API backend)
# ═══════════════════════════════════════════════════════════════
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "http://sheer-lilas-66655t-83ea94e0.koyeb.app"  # ← your API FQDN
).rstrip("/")


# ═══════════════════════════════════════════════════════════════
# API Endpoint Helpers
# ═══════════════════════════════════════════════════════════════

SEARCH_URL   = f"{API_BASE_URL}/api/search"
TRENDING_URL = f"{API_BASE_URL}/api/trending"
SONG_URL     = f"{API_BASE_URL}/api/song"    # append /<song_id>


def get_search_url(query: str, limit: int = 20) -> str:
    """Build search API URL with query parameters."""
    return f"{SEARCH_URL}?{urlencode({'q': query, 'limit': limit})}"


def get_trending_url(limit: int = 20) -> str:
    """Build trending API URL with limit parameter."""
    return f"{TRENDING_URL}?{urlencode({'limit': limit})}"


def get_song_url(song_id: str) -> str:
    """Build song detail API URL."""
    return f"{SONG_URL}/{song_id}"


# ═══════════════════════════════════════════════════════════════
# MongoDB Configuration
# ═══════════════════════════════════════════════════════════════

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://username:password@cluster.mongodb.net/evamusic?retryWrites=true&w=majority"
)

MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "evamusic")

# MongoDB Collection Names
MONGO_COLLECTIONS = {
    "users": "users",
    "favorites": "favorites",
    "playlists": "playlists",
    "recently_played": "recently_played",
    "search_history": "search_history",
    "downloads": "downloads"
}


# ═══════════════════════════════════════════════════════════════
# Flask App Settings
# ═══════════════════════════════════════════════════════════════

class Config:
    """Base configuration class for Flask app."""
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "evamusic-secret-key-change-in-production")
    
    # Session settings
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # CORS settings (for API communication)
    CORS_ORIGINS = [WEB_BASE_URL, "http://localhost:5000", "http://127.0.0.1:5000"]
    
    # Debug mode
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    MONGO_URI = os.environ.get("MONGO_URI_DEV", MONGO_URI)


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")  # Must be set in production


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    MONGO_DB_NAME = "evamusic_test"


# Config mapping
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}

ENV = os.environ.get("FLASK_ENV", "development")
ACTIVE_CONFIG = config_by_name.get(ENV, DevelopmentConfig)


# ═══════════════════════════════════════════════════════════════
# App Metadata
# ═══════════════════════════════════════════════════════════════

APP_NAME = "EvaMusic"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "A modern music streaming web application"
    
