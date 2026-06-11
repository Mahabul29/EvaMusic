import os
import random
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# ─── JioSaavn API — multiple base URLs for fallback ───────────────────

API_BASES = [
    "https://saavn.dev/api",
    "https://jiosaavn-api-privatecvc2.vercel.app/api",
]

def _get(path, params=None, timeout=12):
    """Try each API base in order, return parsed JSON or None."""
    for base in API_BASES:
        try:
            url = f"{base}{path}"
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                # saavn.dev wraps in {"data": ...}, some mirrors use {"result": ...}
                return data
        except Exception as e:
            print(f"[api] {base}{path} failed: {e}")
    return None

# ─── Helpers ──────────────────────────────────────────────────────────

def fetch_songs(query, limit=20):
    data = _get("/search/songs", {"query": query, "limit": limit})
    if not data:
        return []
    # Handle both wrapper shapes
    inner = data.get("data") or data.get("results") or data
    if isinstance(inner, dict):
        return inner.get("results", [])
    if isinstance(inner, list):
        return inner
    return []

def fetch_trending(limit=20):
    queries = ["trending bollywood", "top hindi hits", "viral songs 2024", "new releases india"]
    query = random.choice(queries)
    return fetch_songs(query, limit)

def fetch_playlist_songs(playlist_id):
    data = _get("/playlists", {"id": playlist_id})
    if not data:
        return []
    inner = data.get("data") or data
    if isinstance(inner, dict):
        return inner.get("songs", [])
    return []

def fetch_album_songs(album_id):
    data = _get("/albums", {"id": album_id})
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
    """
    downloadUrl is a list like:
      [{"quality":"96kbps","url":"..."}, {"quality":"160kbps","url":"..."}, ...]
    Pick highest quality non-empty URL.
    """
    if not download_list or not isinstance(download_list, list):
        return ""
    # Sort by quality descending (320 > 160 > 96)
    for quality in ["320kbps", "160kbps", "96kbps"]:
        for item in download_list:
            if isinstance(item, dict) and item.get("quality") == quality:
                u = item.get("url", "")
                if u:
                    return u
    # Fallback: last non-empty URL
    for item in reversed(download_list):
        u = item.get("url", "") if isinstance(item, dict) else ""
        if u:
            return u
    return ""

def format_song(song):
    if not song:
        return {}
    return {
        "id":       song.get("id", ""),
        "title":    song.get("name", song.get("title", "Unknown Title")),
        "artist":   ", ".join(
                        [a.get("name", "") for a in
                         song.get("artists", {}).get("primary", [])]
                    ) or song.get("primaryArtists", "Unknown Artist"),
        "album":    song.get("album", {}).get("name", song.get("album", "Unknown Album"))
                    if isinstance(song.get("album"), dict)
                    else song.get("album", "Unknown Album"),
        "image":    (song.get("image") or [{}])[-1].get("url", "/static/images/default-album.png")
                    if isinstance(song.get("image"), list)
                    else song.get("image", "/static/images/default-album.png"),
        "url":      _best_url(song.get("downloadUrl", song.get("download_url", []))),
        "duration": song.get("duration", 0),
        "year":     song.get("year", ""),
    }

# ─── Routes ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    trending = fetch_trending(12)
    songs = [s for s in [format_song(x) for x in trending] if s.get("url")]
    return render_template('index.html', songs=songs, title="Home")

@app.route('/search')
def search():
    query = request.args.get('q', '')
    songs = []
    if query:
        results = fetch_songs(query, 30)
        songs = [s for s in [format_song(x) for x in results] if s.get("url")]
    return render_template('search.html', songs=songs, query=query, title="Search")

@app.route('/player/<song_id>')
def player(song_id):
    data = _get(f"/songs/{song_id}")
    try:
        song_data = (data.get("data") or [{}])[0] if data else {}
        song = format_song(song_data)
        if not song.get("url"):
            raise ValueError("No stream URL")
    except Exception as e:
        print(f"[player] {e}")
        song = {"id": song_id, "title": "Unknown", "artist": "Unknown",
                "url": "", "image": "/static/images/default-album.png"}
    return render_template('player.html', song=song, title=song.get("title", "Player"))

@app.route('/trending')
def trending():
    songs_raw = fetch_trending(24)
    songs = [s for s in [format_song(x) for x in songs_raw] if s.get("url")]
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

# ─── API Endpoints ────────────────────────────────────────────────────

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
        song_data = (data.get("data") or [{}])[0] if data else {}
        return jsonify(format_song(song_data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Debug endpoint (remove in production) ────────────────────────────

@app.route('/api/debug/search')
def api_debug_search():
    """Test what raw data comes back from the API."""
    query = request.args.get('q', 'arijit singh')
    data = _get("/search/songs", {"query": query, "limit": 3})
    return jsonify(data)

# ─── Static & Error Handlers ──────────────────────────────────────────

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html', title="Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ─── Run ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    
