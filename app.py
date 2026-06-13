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

def fetch_songs(query, limit=20):
    data = _call(get_search_url(query, limit))
    if isinstance(data, list) and data:
        print(f"[SEARCH] '{query}' -> {len(data)} songs")
        return data
    print(f"[SEARCH] No results for '{query}'")
    return []

def fetch_trending(limit=20):
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
        db.save_search_query(get_user_id(), query)
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
    if song.get("id"):
        db.add_to_recently_played(get_user_id(), {
            "song_id": song.get("id"),
            "title": song.get("title", "Unknown"),
            "artist": song.get("artist", "Unknown"),
            "image_url": song.get("image", "")
        })
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
    return render_template('settingsworker.html', title="Settings")

@app.route('/home')
def home():
    songs = fetch_trending(20)
    return render_template('home.html', songs=songs, title="Your Daily Mix")

@app.route('/profile')
def profile():
    user_id = get_user_id()
    favorites = db.get_user_favorites(user_id)
    playlists = db.get_user_playlists(user_id)
    recent = db.get_recently_played(user_id, 5)
    
    stats = {
        "total_favorites": len(favorites),
        "total_playlists": len(playlists),
        "total_plays": len(db.get_recently_played(user_id, 9999)),
        "listening_hours": round(len(db.get_recently_played(user_id, 9999)) * 3.5 / 60, 1)
    }
    
    user_doc = db.get_collection("users").find_one({"user_id": user_id})
    if user_doc:
        profile_data = {
            "username": user_doc.get("username", "EvaUser"),
            "display_name": user_doc.get("username", "EvaUser"),
            "bio": "Music lover 🎵",
            "avatar_url": "/static/images/default-album.png",
            "social_links": {"instagram": "", "twitter": "", "youtube": "", "spotify": ""}
        }
    else:
        profile_data = {
            "username": "EvaUser",
            "display_name": "EvaUser",
            "bio": "Music lover 🎵",
            "avatar_url": "/static/images/default-album.png",
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
        "username": user_doc.get("username", "EvaUser") if user_doc else "EvaUser",
        "display_name": user_doc.get("username", "EvaUser") if user_doc else "EvaUser",
        "bio": "Music lover 🎵",
        "avatar_url": "/static/images/default-album.png",
        "social_links": {"instagram": "", "twitter": "", "youtube": "", "spotify": ""}
    }
    return render_template('edit_profile.html', title="Edit Profile", profile=profile_data)

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
        "song_id": data.get("song_id"),
        "title": data.get("title", "Unknown"),
        "artist": data.get("artist", "Unknown"),
        "album": data.get("album", ""),
        "duration": data.get("duration", ""),
        "image_url": data.get("image_url", ""),
        "audio_url": data.get("audio_url", ""),
        "source": data.get("source", "jiosaavn")
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

@app.route('/api/stats')
def api_stats():
    user_id = get_user_id()
    favorites = db.get_user_favorites(user_id)
    playlists = db.get_user_playlists(user_id)
    recent = db.get_recently_played(user_id, 9999)
    
    return jsonify({
        "total_favorites": len(favorites),
        "total_playlists": len(playlists),
        "total_plays": len(recent),
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
        "api_base": API_BASE_URL,
        "api_status": api_status,
        "db_health": db_health
    })

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
