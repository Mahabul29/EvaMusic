"""
EvaMusic — Configuration File
Handles API endpoints and app settings.
"""

import os
from urllib.parse import urlencode


# ═══════════════════════════════════════════════════════════════
# Koyeb App 1 — Website (EvaMusic Frontend)
# ═══════════════════════════════════════════════════════════════
WEB_BASE_URL = os.environ.get(
    "WEB_BASE_URL",
    "http://localhost:8000"
).rstrip("/")


# ═══════════════════════════════════════════════════════════════
# Koyeb App 2 — API (JioSaavn API backend)
# ═══════════════════════════════════════════════════════════════
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "http://sheer-lilas-66655t-83ea94e0.koyeb.app"
).rstrip("/")


# ═══════════════════════════════════════════════════════════════
# API Endpoint Helpers
# ═══════════════════════════════════════════════════════════════

SEARCH_URL   = f"{API_BASE_URL}/api/search"
TRENDING_URL = f"{API_BASE_URL}/api/trending"
SONG_URL     = f"{API_BASE_URL}/api/song"    # append /<song_id>


def get_search_url(query: str, limit: int = 20) -> str:
    return f"{SEARCH_URL}?{urlencode({'q': query, 'limit': limit})}"


def get_trending_url(limit: int = 20) -> str:
    return f"{TRENDING_URL}?urlencode({'limit': limit})}"


def get_song_url(song_id: str) -> str:
    return f"{SONG_URL}/{song_id}"


# ═══════════════════════════════════════════════════════════════
# Google OAuth Settings
# ═══════════════════════════════════════════════════════════════
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


# ═══════════════════════════════════════════════════════════════
# Flask App Settings
# ═══════════════════════════════════════════════════════════════

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "evamusic-secret-key-change-in-production")

    # Use cookie-based sessions (no filesystem needed — works on Koyeb)
    SESSION_TYPE = None
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "evamusic-secret-key-change-in-production")


class TestingConfig(Config):
    TESTING = True
    DEBUG = True


config_by_name = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig
}

ENV = os.environ.get("FLASK_ENV", "production")
ACTIVE_CONFIG = config_by_name.get(ENV, ProductionConfig)


# ═══════════════════════════════════════════════════════════════
# App Metadata
# ═══════════════════════════════════════════════════════════════

APP_NAME        = "EvaMusic"
APP_VERSION     = "1.0.0"
APP_DESCRIPTION = "A modern music streaming web application"
