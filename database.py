"""
EvaMusic — database.py  (updated)
All original functions preserved.
New: toggle_favorite and add_song_to_playlist now also
     call the taste tracker so likes/playlist-adds improve suggestions.
"""

import json
import os
import uuid
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

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


# ── Lazy import of taste tracker to avoid circular imports ─────
def _taste():
    try:
        from user.trackuser import on_song_liked
        return on_song_liked
    except ImportError:
        return None


# ═══════════════════════════════════════════════════════════════
# FAVORITES
# ═══════════════════════════════════════════════════════════════

def add_to_favorites(user_id, song_data):
    data = _load("favorites")
    user_favs = data.get(user_id, [])

    if any(f["song_id"] == song_data.get("song_id") for f in user_favs):
        return {"success": False, "message": "Song already in favorites"}

    user_favs.append({
        "song_id":   song_data.get("song_id"),
        "title":     song_data.get("title"),
        "artist":    song_data.get("artist"),
        "album":     song_data.get("album"),
        "duration":  song_data.get("duration"),
        "image_url": song_data.get("image_url"),
        "audio_url": song_data.get("audio_url"),
        "source":    song_data.get("source", "jiosaavn"),
        "added_at":  datetime.now(timezone.utc).isoformat()
    })

    data[user_id] = user_favs
    _save("favorites", data)

    # ★ Update taste profile — a like is the strongest signal
    on_liked = _taste()
    if on_liked:
        try:
            on_liked(user_id, song_data)
        except Exception:
            pass

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
        result = add_to_favorites(user_id, song_data)   # ← taste hook inside
        result["action"] = "added"
        return result


# ═══════════════════════════════════════════════════════════════
# RECENTLY PLAYED
# ═══════════════════════════════════════════════════════════════

def add_to_recently_played(user_id, song_data):
    data = _load("recently_played")
    user_history = data.get(user_id, [])

    user_history = [h for h in user_history if h.get("song_id") != song_data.get("song_id")]

    user_history.insert(0, {
        "song_id":   song_data.get("song_id"),
        "title":     song_data.get("title"),
        "artist":    song_data.get("artist"),
        "image_url": song_data.get("image_url"),
        "played_at": datetime.now(timezone.utc).isoformat()
    })

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
        "user_id":     user_id,
        "name":        name,
        "description": description,
        "songs":       [],
        "created_at":  datetime.now(timezone.utc).isoformat(),
        "updated_at":  datetime.now(timezone.utc).isoformat()
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

            # ★ Adding to a playlist = implicit like signal
            on_liked = _taste()
            if on_liked:
                try:
                    on_liked(user_id, song_data)
                except Exception:
                    pass

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

    user_history = [h for h in user_history if h.get("query") != query]

    user_history.insert(0, {
        "query":       query,
        "searched_at": datetime.now(timezone.utc).isoformat()
    })

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
        "user_id":       user_id,
        "username":      username,
        "email":         email,
        "password_hash": None,
        "is_guest":      True,
        "created_at":    datetime.now(timezone.utc).isoformat(),
        "last_active":   datetime.now(timezone.utc).isoformat(),
        "preferences":   {"theme": "dark", "language": "en", "notifications": True}
    }
    _save("users", data)
    return {"success": True, "message": "User created"}


def update_user_activity(user_id):
    data = _load("users")
    if user_id in data:
        data[user_id]["last_active"] = datetime.now(timezone.utc).isoformat()
        _save("users", data)


def get_collection(name):
    return _CollectionShim(name)


class _CollectionShim:
    def __init__(self, name):
        self.name = name

    def find_one(self, query):
        data = _load(self.name)
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
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════

def _username_key(username):
    return (username or "").strip().lower()


def get_user_by_username(username):
    users = _load("users")
    uname_index = _load("usernames")
    user_id = uname_index.get(_username_key(username))
    if user_id and user_id in users:
        return users[user_id]
    for uid, u in users.items():
        if _username_key(u.get("username")) == _username_key(username):
            return u
    return None


def username_exists(username):
    return get_user_by_username(username) is not None


def create_account(user_id, username, password, email=None):
    username = (username or "").strip()
    if not username:
        return {"success": False, "message": "Username is required"}
    if len(username) < 3:
        return {"success": False, "message": "Username must be at least 3 characters"}
    if not password or len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters"}
    if username_exists(username):
        return {"success": False, "message": "Username is already taken"}

    users = _load("users")
    uname_index = _load("usernames")
    now = datetime.now(timezone.utc).isoformat()

    if user_id in users:
        record = users[user_id]
        record["username"]      = username
        record["email"]         = email
        record["password_hash"] = generate_password_hash(password)
        record["is_guest"]      = False
        record["updated_at"]    = now
    else:
        record = {
            "user_id":       user_id,
            "username":      username,
            "email":         email,
            "password_hash": generate_password_hash(password),
            "is_guest":      False,
            "created_at":    now,
            "last_active":   now,
            "preferences":   {"theme": "dark", "language": "en", "notifications": True}
        }
        users[user_id] = record

    uname_index[_username_key(username)] = user_id
    _save("users", users)
    _save("usernames", uname_index)
    return {"success": True, "message": "Account created", "user_id": user_id, "username": username}


def verify_login(username, password):
    user = get_user_by_username(username)
    if not user:
        return {"success": False, "message": "Invalid username or password"}

    pw_hash = user.get("password_hash")
    if not pw_hash or not check_password_hash(pw_hash, password):
        return {"success": False, "message": "Invalid username or password"}

    update_user_activity(user["user_id"])
    return {"success": True, "user_id": user["user_id"], "username": user.get("username")}


def change_password(user_id, old_password, new_password):
    users = _load("users")
    user  = users.get(user_id)
    if not user:
        return {"success": False, "message": "Account not found"}

    pw_hash = user.get("password_hash")
    if not pw_hash or not check_password_hash(pw_hash, old_password):
        return {"success": False, "message": "Current password is incorrect"}

    if not new_password or len(new_password) < 6:
        return {"success": False, "message": "New password must be at least 6 characters"}

    if check_password_hash(pw_hash, new_password):
        return {"success": False, "message": "New password must be different from current"}

    user["password_hash"] = generate_password_hash(new_password)
    user["updated_at"]    = datetime.now(timezone.utc).isoformat()
    _save("users", users)
    return {"success": True, "message": "Password updated successfully"}


def merge_guest_data(guest_user_id, target_user_id):
    if guest_user_id == target_user_id:
        return

    for store_name, merge_strategy in [
        ("favorites",       "list_unique_song_id"),
        ("playlists",       "list_extend"),
        ("recently_played", "list_prepend_unique_song_id"),
        ("search_history",  "list_prepend_unique_query"),
    ]:
        data = _load(store_name)
        guest_items = data.get(guest_user_id, [])
        if not guest_items:
            continue
        target_items = data.get(target_user_id, [])

        if merge_strategy == "list_unique_song_id":
            existing_ids = {f.get("song_id") for f in target_items}
            for item in guest_items:
                if item.get("song_id") not in existing_ids:
                    target_items.append(item)
                    existing_ids.add(item.get("song_id"))
        elif merge_strategy == "list_prepend_unique_song_id":
            existing_ids = {h.get("song_id") for h in target_items}
            for item in guest_items:
                if item.get("song_id") not in existing_ids:
                    target_items.append(item)
                    existing_ids.add(item.get("song_id"))
            target_items.sort(key=lambda x: x.get("played_at", ""), reverse=True)
            target_items = target_items[:50]
        elif merge_strategy == "list_prepend_unique_query":
            existing_queries = {h.get("query") for h in target_items}
            for item in guest_items:
                if item.get("query") not in existing_queries:
                    target_items.append(item)
                    existing_queries.add(item.get("query"))
            target_items = target_items[:20]
        else:
            target_items.extend(guest_items)

        data[target_user_id] = target_items
        data.pop(guest_user_id, None)
        _save(store_name, data)


# ═══════════════════════════════════════════════════════════════
# HEALTH & INIT
# ═══════════════════════════════════════════════════════════════

def check_db_health():
    try:
        _save("_health", {"test": "ok"})
        _load("_health")
        return {"status": "healthy", "connected": True, "type": "file_json"}
    except Exception as e:
        return {"status": "unhealthy", "connected": False, "error": str(e)}


def init_db():
    print("✅ File-based database ready (no MongoDB needed)")
    return True
        
