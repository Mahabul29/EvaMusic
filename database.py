import sqlite3
import json
import time

DB_NAME = "evamusic.db"

def get_db():
    """Opens a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables if they do not exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Favorites Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id TEXT,
                song_id TEXT,
                title TEXT,
                artist TEXT,
                image_url TEXT,
                audio_url TEXT,
                duration INTEGER,
                album TEXT,
                created_at REAL,
                PRIMARY KEY (user_id, song_id)
            )
        """)
        
        # 2. History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                song_id TEXT,
                title TEXT,
                artist TEXT,
                image_url TEXT,
                audio_url TEXT,
                duration INTEGER,
                album TEXT,
                played_at REAL
            )
        """)
        
        # 3. Search History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                query TEXT,
                searched_at REAL
            )
        """)
        conn.commit()

# ═══════════════════════════════════════════════════════════════
# FAVORITES CONTROLLERS
# ═══════════════════════════════════════════════════════════════

def add_to_favorites(user_id, song):
    """Adds a song to the user's favorites list."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO favorites 
                (user_id, song_id, title, artist, image_url, audio_url, duration, album, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                str(song.get('id', '')),
                song.get('title', 'Unknown'),
                song.get('artist', 'Unknown'),
                song.get('image', ''),
                song.get('url', ''),
                song.get('duration', 0),
                song.get('album', ''),
                time.time()
            ))
            conn.commit()
            return True
    except Exception as e:
        print(f"[DB ERROR] add_to_favorites: {e}")
        return False

def is_favorite(user_id, song_id):
    """Checks if a specific song is favorited by the user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND song_id = ?", 
            (user_id, str(song_id))
        )
        return cursor.fetchone() is not None

def toggle_favorite(user_id, song):
    """Toggles a song's favorite status. Returns structural results."""
    song_id = str(song.get('id', ''))
    if is_favorite(user_id, song_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM favorites WHERE user_id = ? AND song_id = ?", 
                (user_id, song_id)
            )
            conn.commit()
        return {"success": True, "action": "removed", "is_favorite": False}
    else:
        success = add_to_favorites(user_id, song)
        return {"success": success, "action": "added", "is_favorite": success}

def get_user_favorites(user_id):
    """Retrieves all favorites for a user sorted by newest addition."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC", 
            (user_id,)
        )
        rows = cursor.fetchall()
        
    return [{
        "id": row["song_id"],
        "title": row["title"],
        "artist": row["artist"],
        "image": row["image_url"],
        "url": row["audio_url"],
        "duration": row["duration"],
        "album": row["album"]
    } for row in rows]

# ═══════════════════════════════════════════════════════════════
# HISTORY CONTROLLERS
# ═══════════════════════════════════════════════════════════════

def add_to_history(user_id, song):
    """Logs a song into the user's streaming playback history."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history 
                (user_id, song_id, title, artist, image_url, audio_url, duration, album, played_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                str(song.get('id', '')),
                song.get('title', 'Unknown'),
                song.get('artist', 'Unknown'),
                song.get('image', ''),
                song.get('url', ''),
                song.get('duration', 0),
                song.get('album', ''),
                time.time()
            ))
            conn.commit()
    except Exception as e:
        print(f"[DB ERROR] add_to_history: {e}")

def get_recently_played(user_id, limit=30):
    """Gets the user's recent streaming history playback row data."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM history WHERE user_id = ? 
            ORDER BY played_at DESC LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        
    return [{
        "id": row["id"],
        "song_id": row["song_id"],
        "title": row["title"],
        "artist": row["artist"],
        "image_url": row["image_url"],
        "image": row["image_url"],  # Fallback property match
        "url": row["audio_url"],
        "duration": row["duration"],
        "album": row["album"],
        "played_at": row["played_at"]
    } for row in rows]

def clear_history(user_id):
    """Purges all playback records for a user profile."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
        conn.commit()

# ═══════════════════════════════════════════════════════════════
# SEARCH HISTORY & HEALTH
# ═══════════════════════════════════════════════════════════════

def add_to_search_history(user_id, query):
    """Logs a user search term query text field string."""
    if not query.strip():
        return
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO search_history (user_id, query, searched_at) VALUES (?, ?, ?)",
                (user_id, query.strip(), time.time())
            )
            conn.commit()
    except Exception as e:
        print(f"[DB ERROR] add_to_search_history: {e}")

def check_db_health():
    """Runs a internal integrity status diagnostic check on SQLite."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            res = cursor.fetchone()[0]
            return "healthy" if res == "ok" else f"unhealthy: {res}"
    except Exception as e:
        return f"error: {str(e)}"
                    
