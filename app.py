import os
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory
from config import get_search_url, get_trending_url, get_song_url, API_BASE_URL

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

_LAST_GOOD_TRENDING = []

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# ─── API helpers (calls your separate Koyeb API app) ─────────────────────────

def _call(url, timeout=20):
    """GET a URL from the Koyeb API app; return parsed JSON or None."""
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


def fetch_songs(query, limit=20):
    """Search songs via the Koyeb API app."""
    data = _call(get_search_url(query, limit))
    if isinstance(data, list) and data:
        print(f"[SEARCH] '{query}' -> {len(data)} songs")
        return data
    print(f"[SEARCH] No results for '{query}'")
    return []


def fetch_trending(limit=20):
    """Fetch trending songs via the Koyeb API app."""
    global _LAST_GOOD_TRENDING
    data = _call(get_trending_url(limit))
    if isinstance(data, list) and data:
        _LAST_GOOD_TRENDING = data
        return data
    if _LAST_GOOD_TRENDING:
        print("[TRENDING] API failed, serving cached results")
        return _LAST_GOOD_TRENDING
    print("[TRENDING] API failed and no cache")
    return []


def fetch_song(song_id):
    """Fetch a single song by ID via the Koyeb API app."""
    data = _call(get_song_url(song_id))
    if isinstance(data, dict) and data.get("url"):
        return data
    return None


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

# ═══════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    songs = fetch_trending(12)
    print(f"[HOME] {len(songs)} songs")
    return render_template('index.html', songs=songs, title="Home")


@app.route('/search')
def search():
    query = request.args.get('q', '')
    songs = []
    if query:
        songs = fetch_songs(query, 30)
        print(f"[SEARCH] '{query}' -> {len(songs)} streamable")
    return render_template('search.html', songs=songs, query=query, title="Search")


@app.route('/player/<song_id>')
def player(song_id):
    song = fetch_song(song_id)
    if not song:
        song = {
            "id": song_id, "title": "Unknown Song", "artist": "Unknown Artist",
            "album": "Unknown Album", "url": "", "image": "/static/images/default-album.png",
            "duration": 0,
        }
    return render_template('player.html', song=song, title=song.get("title", "Player"))


@app.route('/trending')
def trending():
    songs = fetch_trending(24)
    print(f"[TRENDING] {len(songs)} songs")
    return render_template('trending.html', songs=songs, title="Trending")


@app.route('/library')
def library():
    return render_template('library.html', title="Your Library")


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
    return render_template('artist.html', songs=songs, title="Artist")


@app.route('/offline')
def offline():
    return render_template('offline.html', title="Offline")


@app.route('/settings')
def settings():
    return render_template('settings.html', title="Settings")


@app.route('/home')
def home():
    songs = fetch_trending(20)
    return render_template('home.html', songs=songs, title="Your Daily Mix")


@app.route('/profile')
def profile():
    """Profile page with default demo data."""
    profile_data = {
        "username": "EvaUser",
        "display_name": "EvaUser",
        "bio": "Music lover 🎵",
        "avatar_url": "/static/images/default-album.png",
        "social_links": {
            "instagram": "",
            "twitter": "",
            "youtube": "",
            "spotify": ""
        }
    }
    stats = {
        "total_favorites": 0,
        "total_playlists": 0,
        "total_plays": 0,
        "listening_hours": 0
    }
    return render_template('profile.html',
                         title="Profile",
                         profile=profile_data,
                         stats=stats,
                         recently_played=[],
                         favorites=[],
                         playlists=[])


@app.route('/profile/edit')
def edit_profile():
    """Edit profile page."""
    profile_data = {
        "username": "EvaUser",
        "display_name": "EvaUser",
        "bio": "Music lover 🎵",
        "avatar_url": "/static/images/default-album.png",
        "social_links": {
            "instagram": "",
            "twitter": "",
            "youtube": "",
            "spotify": ""
        }
    }
    return render_template('edit_profile.html', title="Edit Profile", profile=profile_data)

# ═══════════════════════════════════════════════════════════════════════
# API ENDPOINTS (proxies to your Koyeb API app)
# ═══════════════════════════════════════════════════════════════════════

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


@app.route('/api/debug')
def api_debug():
    """Check connectivity to the Koyeb API app."""
    try:
        r = requests.get(f"{API_BASE_URL}/", timeout=10)
        return jsonify({
            "api_base": API_BASE_URL,
            "status": r.status_code,
            "response": r.json(),
        })
    except Exception as e:
        return jsonify({"api_base": API_BASE_URL, "error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════
# STATIC & ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.errorhandler(404)
def not_found(e):
    # Don't render templates for missing static files
    if request.path.startswith('/static/'):
        return jsonify({"error": "Not found"}), 404
    return render_template('index.html', songs=[], title="Not Found"), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
'''

with open('/mnt/agents/output/app.py', 'w') as f:
    f.write(app_py)

print("app.py saved successfully")
print(f"Size: {len(app_py)} characters")
