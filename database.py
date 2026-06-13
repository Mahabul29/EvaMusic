"""
EvaMusic - Simple File-Based Database (no MongoDB needed)
Stores favorites, history, playlists in JSON files.
"""

import json
import os
import uuid
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def _file_path(name):
    return os.path.join(DATA_DIR, f"{name}.json")

def _load(name):
    path = _file_path(name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def _save(name, data):
    path = _file_path(name)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ═══════════════════════════════════════════════════════════════
# FAVORITES
# ═══════════════════════════════════════════════════════════════

def add_to_favorites(user_id, song_data):
    data = _load("favorites")
    user_favs = data.get(user_id, [])
    
    # Check if already exists
    if any(f["song_id"] == song_data.get("song_id") for f in user_favs):
        return {"success": False, "message": "Song already in favorites"}
    
    user_favs.append({
        "song_id": song_data.get("song_id"),
        "title": song_data.get("title"),
        "artist": song_data.get("artist"),
        "album": song_data.get("album"),
        "duration": song_data.get("duration"),
        "image_url": song_data.get("image_url"),
        "audio_url": song_data.get("audio_url"),
        "source": song_data.get("source", "jiosaavn"),
        "added_at": datetime.now(timezone.utc).isoformat()
    })
    
    data[user_id] = user_favs
    _save("favorites", data)
    return {"success": True, "message": "Added to favorites"}


def remove_from_favorites(user_id, song_id):
    data = _load("favorites")
    user_favs = data.get(user_id, [])
    original_len = len(user_favs)
    user_favs = [f for f in user_favs if f["song_id"] != song_id]
    
    if len(user_favs) < original_len:
        data[user_id] = user_favs
        _save("favorites", data)
        return {"success": True, "message": "Removed from favorites"}
    return {"success": False, "message": "Song not found in favorites"}


def get_user_favorites(user_id, limit=50, skip=0):
    data = _load("favorites")
    favs = data.get(user_id, [])
    # Sort by added_at descending
    favs.sort(key=lambda x: x.get("added_at", ""), reverse=True)
    return favs[skip:skip + limit]


def is_song_favorited(user_id, song_id):
    data = _load("favorites")
    user_favs = data.get(user_id, [])
    return any(f["song_id"] == song_id for f in user_favs)


def toggle_favorite(user_id, song_data):
    song_id = song_data.get("song_id")
    if is_song_favorited(user_id, song_id):
        result = remove_from_favorites(user_id, song_id)
        result["action"] = "removed"
        return result
    else:
        result = add_to_favorites(user_id, song_data)
        result["action"] = "added"
        return result


# ═══════════════════════════════════════════════════════════════
# RECENTLY PLAYED
# ═══════════════════════════════════════════════════════════════

def add_to_recently_played(user_id, song_data):
    data = _load("recently_played")
    user_history = data.get(user_id, [])
    
    # Remove existing entry for this song
    user_history = [h for h in user_history if h.get("song_id") != song_data.get("song_id")]
    
    # Add to top
    user_history.insert(0, {
        "song_id": song_data.get("song_id"),
        "title": song_data.get("title"),
        "artist": song_data.get("artist"),
        "image_url": song_data.get("image_url"),
        "played_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Keep only last 50
    user_history = user_history[:50]
    data[user_id] = user_history
    _save("recently_played", data)
    return {"success": True, "message": "Added to recently played"}


def get_recently_played(user_id, limit=20):
    data = _load("recently_played")
    history = data.get(user_id, [])
    return history[:limit]


# ═══════════════════════════════════════════════════════════════
# PLAYLISTS
# ═══════════════════════════════════════════════════════════════

def create_playlist(user_id, name, description=""):
    data = _load("playlists")
    user_playlists = data.get(user_id, [])
    
    playlist = {
        "playlist_id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": name,
        "description": description,
        "songs": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    user_playlists.append(playlist)
    data[user_id] = user_playlists
    _save("playlists", data)
    return {"success": True, "message": "Playlist created", "playlist_id": playlist["playlist_id"]}


def add_song_to_playlist(user_id, playlist_id, song_data):
    data = _load("playlists")
    user_playlists = data.get(user_id, [])
    
    for pl in user_playlists:
        if pl["playlist_id"] == playlist_id:
            pl["songs"].append(song_data)
            pl["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save("playlists", data)
            return {"success": True, "message": "Song added to playlist"}
    return {"success": False, "message": "Playlist not found"}


def get_user_playlists(user_id):
    data = _load("playlists")
    playlists = data.get(user_id, [])
    playlists.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return playlists


# ═══════════════════════════════════════════════════════════════
# SEARCH HISTORY
# ═══════════════════════════════════════════════════════════════

def save_search_query(user_id, query):
    data = _load("search_history")
    user_history = data.get(user_id, [])
    
    # Remove duplicate
    user_history = [h for h in user_history if h.get("query") != query]
    
    user_history.insert(0, {
        "query": query,
        "searched_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Keep only last 20
    user_history = user_history[:20]
    data[user_id] = user_history
    _save("search_history", data)


def get_search_history(user_id, limit=10):
    data = _load("search_history")
    history = data.get(user_id, [])
    return history[:limit]


# ═══════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════

def create_user(user_id, username, email=None):
    data = _load("users")
    if user_id in data:
        return {"success": False, "message": "User already exists"}
    
    data[user_id] = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active": datetime.now(timezone.utc).isoformat(),
        "preferences": {"theme": "dark", "language": "en", "notifications": True}
    }
    _save("users", data)
    return {"success": True, "message": "User created"}


def update_user_activity(user_id):
    data = _load("users")
    if user_id in data:
        data[user_id]["last_active"] = datetime.now(timezone.utc).isoformat()
        _save("users", data)


def get_collection(name):
    """Compatibility shim for direct collection access."""
    return _CollectionShim(name)


class _CollectionShim:
    def __init__(self, name):
        self.name = name
    
    def find_one(self, query):
        data = _load(self.name)
        # Simple query matching
        for key, val in query.items():
            for k, v in data.items():
                if isinstance(v, dict) and v.get(key) == val:
                    return v
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and item.get(key) == val:
                            return item
        return None


# ═══════════════════════════════════════════════════════════════
# HEALTH & INIT
# ═══════════════════════════════════════════════════════════════

def check_db_health():
    try:
        # Test write/read
        _save("_health", {"test": "ok"})
        _load("_health")
        return {"status": "healthy", "connected": True, "type": "file_json"}
    except Exception as e:
        return {"status": "unhealthy", "connected": False, "error": str(e)}


def init_db():
    """No-op for file-based DB — files are created on first write."""
    print("✅ File-based database ready (no MongoDB needed)")
    return True
    
