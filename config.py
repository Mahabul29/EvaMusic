import os

# ─── Koyeb App 1 — Website (EvaMusic Frontend) ────────────────────────────────
WEB_BASE_URL = os.environ.get(
    "WEB_BASE_URL",
    "http://your-evamusicwebsite.koyeb.app"   # ← replace with your website FQDN
).rstrip("/")

# ─── Koyeb App 2 — API (JioSaavn API backend) ─────────────────────────────────
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "http://sheer-lilas-66655t-83ea94e0.koyeb.app"  # ← your API FQDN
).rstrip("/")

# ─── API Endpoint helpers ──────────────────────────────────────────────────────

SEARCH_URL   = f"{API_BASE_URL}/api/search"
TRENDING_URL = f"{API_BASE_URL}/api/trending"
SONG_URL     = f"{API_BASE_URL}/api/song"    # append /<song_id>


def get_search_url(query: str, limit: int = 20) -> str:
    from urllib.parse import urlencode
    return f"{SEARCH_URL}?{urlencode({'q': query, 'limit': limit})}"


def get_trending_url(limit: int = 20) -> str:
    from urllib.parse import urlencode
    return f"{TRENDING_URL}?{urlencode({'limit': limit})}"


def get_song_url(song_id: str) -> str:
    return f"{SONG_URL}/{song_id}"
  
