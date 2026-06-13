import os
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory, session
from config import get_search_url, get_trending_url, get_song_url, API_BASE_URL

import database as db

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

db.init_db()

_LAST_GOOD_TRENDING = []

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

def get_user_id():
    if 'user_id' not in session:
        import uuid
        session['user_id'] = str(uuid.uuid4())
        db.create_user(session['user_id'], f"User_{session['user_id'][:8]}")
    return session['user_id']

def _call(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        print(f"[API] {r.status_code} {url}")
        if r.status_code == 200:
            data = r.json()
            if data:
                return data
    except Exception as e:
        print(f"[API ERROR] {url}: {e}")
    return None

def _extract_audio_url(data):
    """
    Robustly extract audio URL from any JioSaavn API response format.
    Handles nested dicts, lists, and all known key names.
    """
    if not data:
        return ""

    # Known keys that may contain the audio URL
    URL_KEYS = ["url", "downloadUrl", "download_url", "media_url",
                "audio_url", "stream_url", "song_url", "link"]

    def _pick(obj):
        if not isinstance(obj, dict):
            return ""
        for key in URL_KEYS:
            val = obj.get(key)
            if not val:
                continue
            # Some APIs return a list of quality options — pick highest
            if isinstance(val, list) and val:
                entry = val[-1]
                if isinstance(entry, dict):
                    return entry.get("url") or entry.get("link") or ""
                if isinstance(entry, str):
                    return entry
            if isinstance(val, str) and val.startswith("http"):
                return val
        return ""

    # 1. Try top-level
    url = _pick(data)
    if url:
        return url

    # 2. Try common wrapper keys
    for wrapper in ["data", "song", "songs", "result"]:
        inner = data.get(wrapper)
        if isinstance(inner, dict):
            url = _pick(inner)
            if url:
                return url
        elif isinstance(inner, list) and inner:
            url = _pick(inner[0])
            if url:
                return url

    return ""

def _normalize_song(data):
    """
    Normalize any JioSaavn API song dict so the player always gets
    consistent field names: id, title, artist, image, url, duration.
    """
    if not data:
        return None

    # Unwrap wrapper if present
    inner = data
    for wrapper in ["data", "song", "result"]:
        candidate = data.get(wrapper)
        if isinstance(candidate, dict):
            inner = candidate
            break
        elif isinstance(candidate, list) and candidate:
            inner = candidate[0]
            break

    audio_url = _extract_audio_url(data)  # try full data including wrappers
    if not audio_url:
        audio_url = _extract_audio_url(inner)

    # Image: may be a list of quality options
    image = inner.get("image") or inner.get("image_url") or inner.get("thumbnail") or ""
    if isinstance(image, list) and image:
        entry = image[-1]
        image = entry.get("url") or entry.get("link") or (entry if isinstance(entry, str) else "") or ""

    return {
        "id":       inner.get("id") or inner.get("song_id") or data.get("id") or "",
        "title":    inner.get("title") or inner.get("name") or inner.get("song") or "Unknown",
        "artist":   inner.get("artist") or inner.get("primaryArtists") or inner.get("singers") or "Unknown",
        "album":    inner.get("album") or inner.get("album_name") or "",
        "duration": inner.get("duration") or inner.get("length") or 0,
        "image":    image or "/static/images/default-album.png",
        "url":      audio_url,  # always present as "url" so player JS finds it
    }

def fetch_songs(query, limit=20):
    data = _call(get_search_url(query, limit))
    if isinstance(data, list) and data:
        print(f"[SEARCH] '{query}' -> {len(data)} songs")
        return data
    # Some APIs wrap results
    if isinstance(data, dict):
        for key in ["data", "results", "songs"]:
            inner = data.get(key)
            if isinstance(inner, list) and inner:
                print(f"[SEARCH] '{query}' -> {len(inner)} songs (unwrapped)")
                return inner
    print(f"[SEARCH] No results for '{query}'")
    return []

def fetch_trending(limit=20):
    global _LAST_GOOD_TRENDING
    data = _call(get_trending_url(limit))
    if isinstance(data, list) and data:
        _LAST_GOOD_TRENDING = data
        return data
    if isinstance(data, dict):
        for key in ["data", "results", "songs"]:
            inner = data.get(key)
            if isinstance(inner, list) and inner:
                _LAST_GOOD_TRENDING = inner
                return inner
    if _LAST_GOOD_TRENDING:
        print("[TRENDING] API failed, serving cached results")
        return _LAST_GOOD_TRENDING
    print("[TRENDING] API failed and no cache")
    return []

def fetch_song(song_id):
    """
    Fetch a single song and normalize it.
    Returns None only if the API call completely fails.
    """
    data = _call(get_song_url(song_id))
    if not data:
        print(f"[fetch_song] API returned nothing for {song_id}")
        return None

    song = _normalize_song(data)
    if not song:
        print(f"[fetch_song] Could not normalize data for {song_id}: {data}")
        return None

    if not song["url"]:
        print(f"[fetch_song] WARNING: No audio URL found for {song_id}. Raw keys: {list(data.keys())}")
        # Still return the song so the bar shows metadata;
        # player will show "No audio URL available" instead of crashing.

    print(f"[fetch_song] OK: {song['title']} | url={bool(song['url'])}")
    return song

def fetch_playlist_songs(playlist_id):
    data = _call(f"{API_BASE_URL}/api/playlist/{playlist_id}")
    if isinstance(data, list):
        return data
    return []

def fetch_album_songs(album_id):
    data = _call(f"{API_BASE_URL}/api/album/{album_id}")
    if isinstance(data, list):
        return data
    return []

def fetch_artist_songs(artist_id, limit=20):
    data = _call(f"{API_BASE_URL}/api/artist/{artist_id}?limit={limit}")
    if isinstance(data, list):
        return data
    return []

# ── PAGE ROUTES ────────────────────────────────────────────────

@app.route('/')
def index():
    songs = fetch_trending(12)
    print(f"[HOME] {len(songs)} songs")
    return render_template('index.html', songs=songs, title="Home")

@app.route('/home')
def home():
    songs = fetch_trending(20)
    return render_template('home.html', songs=songs, title="Your Daily Mix")

@app.route('/search')
def search():
    query = request.args.get('q', '')
    songs = []
    if query:
        songs = fetch_songs(query, 30)
        db.save_search_query(get_user_id(), query)
        print(f"[SEARCH] '{query}' -> {len(songs)} streamable")
    return render_template('search.html', songs=songs, query=query, title="Search")

@app.route('/trending')
def trending():
    songs = fetch_trending(24)
    print(f"[TRENDING] {len(songs)} songs")
    return render_template('trending.html', songs=songs, title="Trending")

@app.route('/library')
def library():
    return render_template('library.html', title="Your Library")

@app.route('/offline')
def offline():
    return render_template('offline.html', title="Offline")

@app.route('/settings')
def settings():
    return render_template('settingsworker.html', title="Settings")

# ── PLAYER / CONTENT ROUTES ────────────────────────────────────

@app.route('/player/<song_id>')
def player(song_id):
    song = fetch_song(song_id)
    if not song:
        song = {
            "id":       song_id,
            "title":    "Unknown Song",
            "artist":   "Unknown Artist",
            "album":    "Unknown Album",
            "url":      "",
            "image":    "/static/images/default-album.png",
            "duration": 0,
        }
    if song.get("id"):
        db.add_to_recently_played(get_user_id(), {
            "song_id":  song.get("id"),
            "title":    song.get("title", "Unknown"),
            "artist":   song.get("artist", "Unknown"),
            "image_url": song.get("image", "")
        })
    return render_template('player.html', song=song, title=song.get("title", "Player"))

@app.route('/playlist/<playlist_id>')
def playlist(playlist_id):
    songs = fetch_playlist_songs(playlist_id)
    return render_template('playlist.html', songs=songs, title="Playlist")

@app.route('/album/<album_id>')
def album(album_id):
    songs = fetch_album_songs(album_id)
    return render_template('album.html', songs=songs, title="Album")

@app.route('/artist/<artist_id>')
def artist(artist_id):
    songs = fetch_artist_songs(artist_id, 20)
    artist_name = songs[0].get('artist', 'Artist') if songs else 'Artist'
    return render_template('artist.html', songs=songs, title=artist_name)

# ── PROFILE ROUTES ─────────────────────────────────────────────

@app.route('/profile')
def profile():
    user_id = get_user_id()
    favorites = db.get_user_favorites(user_id)
    playlists = db.get_user_playlists(user_id)
    recent = db.get_recently_played(user_id, 5)

    stats = {
        "total_favorites": len(favorites),
        "total_playlists": len(playlists),
        "total_plays":     len(db.get_recently_played(user_id, 9999)),
        "listening_hours": round(len(db.get_recently_played(user_id, 9999)) * 3.5 / 60, 1)
    }

    user_doc = db.get_collection("users").find_one({"user_id": user_id})
    if user_doc:
        profile_data = {
            "username":     user_doc.get("username", "EvaUser"),
            "display_name": user_doc.get("username", "EvaUser"),
            "bio":          "Music lover 🎵",
            "avatar_url":   "/static/images/default-album.png",
            "social_links": {"instagram": "", "twitter": "", "youtube": "", "spotify": ""}
        }
    else:
        profile_data = {
            "username":     "EvaUser",
            "display_name": "EvaUser",
            "bio":          "Music lover 🎵",
            "avatar_url":   "/static/images/default-album.png",
            "social_links": {"instagram": "", "twitter": "", "youtube": "", "spotify": ""}
        }

    return render_template('profile.html',
                           title="Profile",
                           profile=profile_data,
                           stats=stats,
                           recently_played=recent,
                           favorites=favorites[:5],
                           playlists=playlists[:5])

@app.route('/profile/edit')
def edit_profile():
    user_id = get_user_id()
    user_doc = db.get_collection("users").find_one({"user_id": user_id})
    profile_data = {
        "username":     user_doc.get("username", "EvaUser") if user_doc else "EvaUser",
        "display_name": user_doc.get("username", "EvaUser") if user_doc else "EvaUser",
        "bio":          "Music lover 🎵",
        "avatar_url":   "/static/images/default-album.png",
        "social_links": {"instagram": "", "twitter": "", "youtube": "", "spotify": ""}
    }
    return render_template('edit_profile.html', title="Edit Profile", profile=profile_data)

@app.route('/favorites')
def favorites():
    user_id = get_user_id()
    songs = db.get_user_favorites(user_id)
    return render_template('favorites.html', songs=songs, title="My Favorites")

@app.route('/history')
def history():
    user_id = get_user_id()
    songs = db.get_recently_played(user_id, 50)
    return render_template('history.html', songs=songs, title="Listening History")

@app.route('/playlists')
def playlists():
    user_id = get_user_id()
    playlists_data = db.get_user_playlists(user_id)
    return render_template('playlists.html', playlists=playlists_data, title="My Playlists")

# ── API ROUTES ─────────────────────────────────────────────────

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    songs = fetch_songs(query, limit)
    return jsonify(songs)

@app.route('/api/trending')
def api_trending():
    limit = request.args.get('limit', 20, type=int)
    songs = fetch_trending(limit)
    return jsonify(songs)

@app.route('/api/song/<song_id>')
def api_song(song_id):
    song = fetch_song(song_id)
    if song:
        return jsonify(song)
    return jsonify({"error": "Song not found"}), 404

@app.route('/api/favorite', methods=['POST'])
def api_toggle_favorite():
    user_id = get_user_id()
    data = request.get_json() or {}
    song_data = {
        "song_id":   data.get("song_id"),
        "title":     data.get("title", "Unknown"),
        "artist":    data.get("artist", "Unknown"),
        "album":     data.get("album", ""),
        "duration":  data.get("duration", ""),
        "image_url": data.get("image_url") or data.get("image", ""),
        "audio_url": data.get("audio_url") or data.get("url", ""),
        "source":    data.get("source", "jiosaavn")
    }
    result = db.toggle_favorite(user_id, song_data)
    return jsonify(result)

@app.route('/api/favorites')
def api_get_favorites():
    user_id = get_user_id()
    favorites = db.get_user_favorites(user_id)
    return jsonify(favorites)

@app.route('/api/history')
def api_get_history():
    user_id = get_user_id()
    limit = request.args.get('limit', 20, type=int)
    history = db.get_recently_played(user_id, limit)
    return jsonify(history)

@app.route('/api/search-history')
def api_search_history():
    user_id = get_user_id()
    limit = request.args.get('limit', 10, type=int)
    history = db.get_search_history(user_id, limit)
    return jsonify([h["query"] for h in history])

@app.route('/api/playlist/create', methods=['POST'])
def api_create_playlist():
    user_id = get_user_id()
    data = request.get_json() or {}
    name = data.get("name", "My Playlist")
    description = data.get("description", "")
    result = db.create_playlist(user_id, name, description)
    return jsonify(result)

@app.route('/api/playlist/<playlist_id>/add', methods=['POST'])
def api_add_to_playlist(playlist_id):
    user_id = get_user_id()
    data = request.get_json() or {}
    result = db.add_song_to_playlist(user_id, playlist_id, data)
    return jsonify(result)

@app.route('/api/playlists')
def api_get_playlists():
    user_id = get_user_id()
    playlists_data = db.get_user_playlists(user_id)
    return jsonify(playlists_data)

@app.route('/api/stats')
def api_stats():
    user_id = get_user_id()
    favorites = db.get_user_favorites(user_id)
    playlists_data = db.get_user_playlists(user_id)
    recent = db.get_recently_played(user_id, 9999)
    return jsonify({
        "total_favorites": len(favorites),
        "total_playlists": len(playlists_data),
        "total_plays":     len(recent),
        "listening_hours": round(len(recent) * 3.5 / 60, 1)
    })

@app.route('/api/debug')
def api_debug():
    try:
        r = requests.get(f"{API_BASE_URL}/", timeout=10)
        api_status = r.status_code
    except Exception as e:
        api_status = f"error: {e}"

    db_health = db.check_db_health()
    return jsonify({
        "api_base":   API_BASE_URL,
        "api_status": api_status,
        "db_health":  db_health
    })

# ── DEBUG: inspect raw API response for any song ──────────────
@app.route('/api/debug/song/<song_id>')
def api_debug_song(song_id):
    """Shows raw API response so you can see exactly what fields come back."""
    raw  = _call(get_song_url(song_id))
    norm = _normalize_song(raw) if raw else None
    return jsonify({
        "raw":        raw,
        "normalized": norm,
        "audio_url_found": bool(norm and norm.get("url"))
    })

# ── STATIC & ERRORS ────────────────────────────────────────────

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/static/'):
        return jsonify({"error": "Not found"}), 404
    return render_template('index.html', songs=[], title="Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    import traceback
    print(f"[500 ERROR] {e}")
    print(traceback.format_exc())
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
        
