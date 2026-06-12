import os
import random
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# ═══════════════════════════════════════════════════════════════════════
# WORKING JioSaavn API endpoints (verified June 2026)
# ═══════════════════════════════════════════════════════════════════════

API_BASES = [
    "https://saavn.dev/api",                            # ✅ Primary — standard REST API
    "https://jio-saavn-api.vercel.app",                 # ✅ Fallback
    "https://jiosaavn-api-privatecvc2.vercel.app/api",  # Fallback
]

def _get(path, params=None, timeout=15):
    """Try each API base in order; only return data that is non-empty."""
    for base in API_BASES:
        try:
            url = f"{base}{path}"
            r = requests.get(url, params=params, timeout=timeout)
            print(f"[API] {r.status_code} from {url}")
            if r.status_code == 200:
                data = r.json()
                # Don't return a 200 that carries no usable content
                if data and data != {} and data != []:
                    return data
                print(f"[API] Empty body from {url}, trying next base")
        except Exception as e:
            print(f"[API ERROR] {base}{path}: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════════
# FIXED fetch_songs — handles different API response shapes
# ═══════════════════════════════════════════════════════════════════════

def fetch_songs(query, limit=20):
    """
    Try multiple endpoint patterns since different mirrors use different paths.
    saavn.dev uses /search/songs?query=...
    jio-saavn-api uses /search?query=...
    """
    endpoints_to_try = [
        ("/search/songs", {"query": query, "limit": limit}),
        ("/search/songs", {"q": query, "limit": limit}),
        ("/search", {"query": query, "limit": limit}),
        ("/search", {"q": query, "limit": limit}),
    ]

    for path, params in endpoints_to_try:
        data = _get(path, params)
        if data:
            songs = _extract_songs(data)
            if songs:
                print(f"[SEARCH] '{query}' → {len(songs)} raw songs via {path}")
                return songs
    print(f"[SEARCH] No results found for '{query}'")
    return []

def _extract_songs(data):
    """Extract song list from various API response wrappers."""
    if not data:
        return []
    
    # Handle {"data": {"results": [...]}}  (saavn.dev)
    # Handle {"results": [...]}             (direct)
    # Handle {"data": [...]}                (array wrapper)
    # Handle [...]                          (direct array)
    
    candidates = [
        data.get("data", {}).get("results") if isinstance(data.get("data"), dict) else None,
        data.get("data"),
        data.get("results"),
        data.get("result"),
        data,
    ]
    
    for candidate in candidates:
        if isinstance(candidate, list) and len(candidate) > 0:
            return candidate
    return []

def fetch_trending(limit=20):
    queries = [
        "trending bollywood 2024",
        "top hindi songs",
        "arijit singh hits",
        "bollywood new releases",
        "viral songs india"
    ]
    query = random.choice(queries)
    return fetch_songs(query, limit)

def fetch_playlist_songs(playlist_id):
    data = _get(f"/playlists", {"id": playlist_id})
    if not data:
        return []
    inner = data.get("data") or data
    if isinstance(inner, dict):
        return inner.get("songs", [])
    return []

def fetch_album_songs(album_id):
    data = _get(f"/albums", {"id": album_id})
    if not data:
        return []
    inner = data.get("data") or data
    if isinstance(inner, dict):
        return inner.get("songs", [])
    return []

def fetch_artist_songs(artist_id, limit=20):
    data = _get(f"/artists/{artist_id}/songs", {"limit": limit})
    if not data:
        return []
    inner = data.get("data") or data
    if isinstance(inner, dict):
        return inner.get("songs", [])
    return []

def _best_url(download_list):
    """Pick highest quality non-empty URL from downloadUrl array."""
    if not download_list or not isinstance(download_list, list):
        return ""
    for quality in ["320kbps", "160kbps", "96kbps"]:
        for item in download_list:
            if isinstance(item, dict) and item.get("quality") == quality:
                u = item.get("url", "")
                if u:
                    return u
    for item in reversed(download_list):
        u = item.get("url", "") if isinstance(item, dict) else ""
        if u:
            return u
    return ""

def format_song(song):
    if not song:
        return {}
    
    # Handle different image formats
    image = song.get("image", "/static/images/default-album.png")
    if isinstance(image, list) and image:
        image = image[-1].get("url", "/static/images/default-album.png")
    elif isinstance(image, dict):
        image = image.get("url", "/static/images/default-album.png")
    elif not isinstance(image, str):
        image = "/static/images/default-album.png"
    
    # Handle artists (can be array, dict, or string)
    artists = song.get("artists", {})
    if isinstance(artists, dict):
        primary = artists.get("primary", [])
        artist_names = [a.get("name", "") for a in primary if isinstance(a, dict)]
        artist = ", ".join(artist_names) if artist_names else song.get("primaryArtists", "Unknown Artist")
    elif isinstance(artists, list):
        artist = ", ".join([a.get("name", "") for a in artists if isinstance(a, dict)]) or "Unknown Artist"
    else:
        artist = song.get("primaryArtists", song.get("artist", "Unknown Artist"))
    
    # Handle album
    album = song.get("album", "Unknown Album")
    if isinstance(album, dict):
        album = album.get("name", "Unknown Album")
    
    return {
        "id":       str(song.get("id", "")),
        "title":    song.get("name", song.get("title", "Unknown Title")),
        "artist":   artist,
        "album":    album,
        "image":    image,
        "url":      _best_url(song.get("downloadUrl", song.get("download_url", []))),
        "duration": song.get("duration", 0),
        "year":     song.get("year", ""),
    }

# ═══════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    trending = fetch_trending(12)
    songs = [format_song(x) for x in trending]
    songs_with_url = [s for s in songs if s.get("url")]
    print(f"[HOME] {len(songs_with_url)}/{len(songs)} songs have stream URLs")
    return render_template('index.html', songs=songs_with_url, title="Home")

@app.route('/search')
def search():
    query = request.args.get('q', '')
    songs = []
    if query:
        results = fetch_songs(query, 30)
        # Keep all songs; mark those without a URL so the UI can grey them out
        songs = [format_song(x) for x in results]
        songs_with_url = [s for s in songs if s.get("url")]
        print(f"[SEARCH] Query: '{query}' → {len(songs)} total, {len(songs_with_url)} streamable")
    return render_template('search.html', songs=songs, query=query, title="Search")

@app.route('/player/<song_id>')
def player(song_id):
    data = _get(f"/songs/{song_id}")
    try:
        if data and isinstance(data.get("data"), list):
            song_data = data["data"][0]
        elif data and isinstance(data.get("data"), dict):
            song_data = data["data"]
        else:
            song_data = data or {}
        song = format_song(song_data)
        if not song.get("url"):
            raise ValueError("No stream URL")
    except Exception as e:
        print(f"[PLAYER ERROR] {e}")
        song = {
            "id": song_id,
            "title": "Unknown Song",
            "artist": "Unknown Artist",
            "album": "Unknown Album",
            "url": "",
            "image": "/static/images/default-album.png",
            "duration": 0
        }
    return render_template('player.html', song=song, title=song.get("title", "Player"))

@app.route('/trending')
def trending():
    songs_raw = fetch_trending(24)
    songs = [s for s in [format_song(x) for x in songs_raw] if s.get("url")]
    print(f"[TRENDING] {len(songs)} streamable songs")
    return render_template('trending.html', songs=songs, title="Trending")

@app.route('/library')
def library():
    return render_template('library.html', title="Your Library")

@app.route('/playlist/<playlist_id>')
def playlist(playlist_id):
    songs_raw = fetch_playlist_songs(playlist_id)
    songs = [format_song(s) for s in songs_raw]
    return render_template('playlist.html', songs=songs, title="Playlist")

@app.route('/album/<album_id>')
def album(album_id):
    songs_raw = fetch_album_songs(album_id)
    songs = [format_song(s) for s in songs_raw]
    return render_template('album.html', songs=songs, title="Album")

@app.route('/artist/<artist_id>')
def artist(artist_id):
    songs_raw = fetch_artist_songs(artist_id, 20)
    songs = [format_song(s) for s in songs_raw]
    return render_template('artist.html', songs=songs, title="Artist")

@app.route('/offline')
def offline():
    return render_template('offline.html', title="Offline")

# ═══════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    results = fetch_songs(query, limit)
    songs = [s for s in [format_song(x) for x in results] if s.get("url")]
    return jsonify(songs)

@app.route('/api/trending')
def api_trending():
    limit = request.args.get('limit', 20, type=int)
    results = fetch_trending(limit)
    songs = [s for s in [format_song(x) for x in results] if s.get("url")]
    return jsonify(songs)

@app.route('/api/song/<song_id>')
def api_song(song_id):
    data = _get(f"/songs/{song_id}")
    try:
        if data and isinstance(data.get("data"), list):
            song_data = data["data"][0]
        elif data and isinstance(data.get("data"), dict):
            song_data = data["data"]
        else:
            song_data = data or {}
        return jsonify(format_song(song_data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug/search')
def api_debug_search():
    """Test what raw data comes back from the API."""
    query = request.args.get('q', 'arijit singh')
    data = _get("/search/songs", {"query": query, "limit": 3})
    return jsonify({
        "api_response": data,
        "extracted_songs": _extract_songs(data),
        "formatted": [format_song(s) for s in (_extract_songs(data) or [])]
    })

# ═══════════════════════════════════════════════════════════════════════
# STATIC & ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html', title="Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ═══════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

    
