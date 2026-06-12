import os
import random
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# ═══════════════════════════════════════════════════════════════════════
# API configs — (base, search_path, param_key)
# ═══════════════════════════════════════════════════════════════════════

SEARCH_CONFIGS = [
    ("https://jiosaavn-api-2.vercel.app",    "/api/search/songs", "query"),
    ("https://jiosaavn-api-ts.vercel.app",   "/api/search/songs", "query"),
    ("https://jiosaavn-api-sigma.vercel.app","/api/search/songs", "query"),
    ("https://jio-saavn-api.vercel.app",     "/search/songs",     "query"),
    ("https://jio-saavn-api.vercel.app",     "/search",           "query"),
]

# For song detail lookups (non-search)
API_BASES = [
    "https://jiosaavn-api-2.vercel.app/api",
    "https://jiosaavn-api-ts.vercel.app/api",
    "https://jio-saavn-api.vercel.app",
]

def _get(url, params=None, timeout=15):
    """GET a full URL; return parsed JSON only if non-empty."""
    try:
        r = requests.get(url, params=params, timeout=timeout)
        print(f"[API] {r.status_code} from {url}")
        if r.status_code == 200:
            data = r.json()
            if data and data != {} and data != []:
                return data
            print(f"[API] Empty body from {url}")
    except Exception as e:
        print(f"[API ERROR] {url}: {e}")
    return None

def _get_path(path, params=None, timeout=15):
    """Try path against each base in API_BASES."""
    for base in API_BASES:
        data = _get(f"{base}{path}", params, timeout)
        if data:
            return data
    return None

# ═══════════════════════════════════════════════════════════════════════

def fetch_songs(query, limit=20):
    for base, path, key in SEARCH_CONFIGS:
        data = _get(f"{base}{path}", {key: query, "limit": limit})
        if data:
            songs = _extract_songs(data)
            if songs:
                print(f"[SEARCH] '{query}' → {len(songs)} songs via {base}{path}")
                return songs
    print(f"[SEARCH] No results for '{query}'")
    return []

def _extract_songs(data):
    if not data:
        return []
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
    return fetch_songs(random.choice(queries), limit)

def fetch_playlist_songs(playlist_id):
    data = _get_path(f"/playlists", {"id": playlist_id})
    if not data:
        return []
    inner = data.get("data") or data
    if isinstance(inner, dict):
        return inner.get("songs", [])
    return []

def fetch_album_songs(album_id):
    data = _get_path(f"/albums", {"id": album_id})
    if not data:
        return []
    inner = data.get("data") or data
    if isinstance(inner, dict):
        return inner.get("songs", [])
    return []

def fetch_artist_songs(artist_id, limit=20):
    data = _get_path(f"/artists/{artist_id}/songs", {"limit": limit})
    if not data:
        return []
    inner = data.get("data") or data
    if isinstance(inner, dict):
        return inner.get("songs", [])
    return []

def _best_url(download_list):
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
    image = song.get("image", "/static/images/default-album.png")
    if isinstance(image, list) and image:
        image = image[-1].get("url", "/static/images/default-album.png")
    elif isinstance(image, dict):
        image = image.get("url", "/static/images/default-album.png")
    elif not isinstance(image, str):
        image = "/static/images/default-album.png"

    artists = song.get("artists", {})
    if isinstance(artists, dict):
        primary = artists.get("primary", [])
        artist_names = [a.get("name", "") for a in primary if isinstance(a, dict)]
        artist = ", ".join(artist_names) if artist_names else song.get("primaryArtists", "Unknown Artist")
    elif isinstance(artists, list):
        artist = ", ".join([a.get("name", "") for a in artists if isinstance(a, dict)]) or "Unknown Artist"
    else:
        artist = song.get("primaryArtists", song.get("artist", "Unknown Artist"))

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
        songs = [format_song(x) for x in results]
        songs_with_url = [s for s in songs if s.get("url")]
        print(f"[SEARCH] '{query}' → {len(songs)} total, {len(songs_with_url)} streamable")
    return render_template('search.html', songs=songs, query=query, title="Search")

@app.route('/player/<song_id>')
def player(song_id):
    data = _get_path(f"/songs/{song_id}")
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
            "id": song_id, "title": "Unknown Song", "artist": "Unknown Artist",
            "album": "Unknown Album", "url": "", "image": "/static/images/default-album.png",
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
    data = _get_path(f"/songs/{song_id}")
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
    query = request.args.get('q', 'arijit singh')
    results = []
    for base, path, key in SEARCH_CONFIGS:
        url = f"{base}{path}"
        data = _get(url, {key: query, "limit": 3})
        results.append({"url": url, "got_data": bool(data), "songs": len(_extract_songs(data)) if data else 0})
    return jsonify(results)

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
