"""
EvaMusic — database.py (JSON Native Storage)
All native features integrated seamlessly to prevent dashboard crashes.
"""

import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def _file_path(name):
    return os.path.join(DATA_DIR, f"{name}.json")

def _load(name):
    path = _file_path(name)
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def _save(name, data):
    path = _file_path(name)
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def init_db():
    """Ensures structure files exist on initialization."""
    for name in ["favorites", "history", "search_history"]:
        if not os.path.exists(_file_path(name)):
            _save(name, {})

# ═══════════════════════════════════════════════════════════════
# FAVORITES CONTROLLERS
# ═══════════════════════════════════════════════════════════════

def add_to_favorites(user_id, song_data):
    data = _load("favorites")
    if user_id not in data:
        data[user_id] = []
    
    if not any(s.get('id') == song_data.get('id') for s in data[user_id]):
        song_entry = {
            "id": song_data.get("id"),
            "title": song_data.get("title", "Unknown"),
            "artist": song_data.get("artist", "Unknown"),
            "album": song_data.get("album", ""),
            "duration": song_data.get("duration", 0),
            "image": song_data.get("image", "/static/images/default-album.png"),
            "url": song_data.get("url", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        data[user_id].append(song_entry)
        _save("favorites", data)
    return True

def is_favorite(user_id, song_id):
    data = _load("favorites")
    user_favs = data.get(user_id, [])
    return any(str(s.get('id')) == str(song_id) for s in user_favs)

def toggle_favorite(user_id, song_data):
    song_id = song_data.get('id')
    data = _load("favorites")
    user_favs = data.get(user_id, [])
    
    if is_favorite(user_id, song_id):
        data[user_id] = [s for s in user_favs if str(s.get('id')) != str(song_id)]
        _save("favorites", data)
        return {"success": True, "action": "removed", "is_favorite": False}
    else:
        add_to_favorites(user_id, song_data)
        return {"success": True, "action": "added", "is_favorite": True}

def get_user_favorites(user_id):
    data = _load("favorites")
    return data.get(user_id, [])

# ═══════════════════════════════════════════════════════════════
# HISTORY CONTROLLERS
# ═══════════════════════════════════════════════════════════════

def add_to_history(user_id, song_data):
    data = _load("history")
    if user_id not in data:
        data[user_id] = []
    
    history_entry = {
        "song_id": song_data.get("id") or song_data.get("song_id"),
        "title": song_data.get("title", "Unknown"),
        "artist": song_data.get("artist", "Unknown"),
        "image_url": song_data.get("image") or song_data.get("image_url", "/static/images/default-album.png"),
        "audio_url": song_data.get("url") or song_data.get("audio_url", ""),
        "played_at": datetime.now(timezone.utc).isoformat()
    }
    data[user_id].insert(0, history_entry)
    data[user_id] = data[user_id][:50]
    _save("history", data)

def add_to_recently_played(user_id, song_data):
    """Bridge fallback to connect refresh_bp smoothly."""
    add_to_history(user_id, song_data)

def get_recently_played(user_id, limit=30):
    data = _load("history")
    return data.get(user_id, [])[:limit]

def clear_history(user_id):
    data = _load("history")
    if user_id in data:
        data[user_id] = []
        _save("history", data)

# ═══════════════════════════════════════════════════════════════
# UTILITIES & SEARCH
# ═══════════════════════════════════════════════════════════════

def add_to_search_history(user_id, query):
    if not query.strip():
        return
    data = _load("search_history")
    if user_id not in data:
        data[user_id] = []
    data[user_id].insert(0, {"query": query.strip(), "searched_at": datetime.now(timezone.utc).isoformat()})
    data[user_id] = data[user_id][:20]
    _save("search_history", data)

def check_db_health():
    return {"status": "healthy", "connected": True, "type": "file_json"}
    
