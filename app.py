import os
import requests
import uuid
import html
from flask import Flask, render_template, jsonify, request, session
from config import get_search_url, get_trending_url, get_song_url, API_BASE_URL

import database as db
from routes import profile_bp

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-to-something-random-abc123_2026')

app.register_blueprint(profile_bp)
db.init_db()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
    return session['user_id']

def is_logged_in():
    return bool(session.get('logged_in'))

def _call(url, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] {url}: {e}")
    return None

def _extract_audio_url(data):
    if not data:
        return ""
    URL_KEYS = ["url", "downloadUrl", "download_url", "media_url",
                "audio_url", "stream_url", "song_url", "link"]

    def _pick(obj):
        if not isinstance(obj, dict):
            return ""
        for key in URL_KEYS:
            val = obj.get(key)
            if not val:
                continue
            if isinstance(val, list) and val:
                entry = val[-1]
                if isinstance(entry, dict):
                    return entry.get("url") or entry.get("link") or ""
                if isinstance(entry, str):
                    return entry
            if isinstance(val, str) and val.startswith("http"):
                return val
        return ""

    url = _pick(data)
    if url:
        return url

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
    if not data:
        return None

    inner = data
    for wrapper in ["data", "song", "result"]:
        candidate = data.get(wrapper)
        if isinstance(candidate, dict):
            inner = candidate
            break
        elif isinstance(candidate, list) and candidate:
            inner = candidate[0]
            break

    audio_url = _extract_audio_url(data)
    if not audio_url:
        audio_url = _extract_audio_url(inner)

    image = inner.get("image") or inner.get("image_url") or inner.get("thumbnail") or ""
    if isinstance(image, list) and image:
        entry = image[-1]
        image = entry.get("url") or entry.get("link") or (entry if isinstance(entry, str) else "") or ""

    title = inner.get("title") or inner.get("name") or inner.get("song") or "Unknown Song"
    artist = inner.get("artist") or inner.get("primaryArtists") or inner.get("singers") or "Unknown Artist"
    album = inner.get("album") or inner.get("album_name") or ""

    if isinstance(title, str): title = html.unescape(title)
    if isinstance(artist, str): artist = html.unescape(artist)
    if isinstance(album, str): album = html.unescape(album)

    return {
        "id":       str(inner.get("id") or inner.get("song_id") or data.get("id") or ""),
        "title":    title,
        "artist":   artist,
        "album":    album,
        "duration": int(inner.get("duration") or inner.get("length") or 0),
        "image":    image or "/static/images/default-album.png",
        "url":      audio_url,
    }

def fetch_songs(query, limit=20):
    data = _call(get_search_url(query, limit))
    if isinstance(data, list) and data:
        return data
    if isinstance(data, dict):
        for key in ["data", "results", "songs"]:
            inner = data.get(key)
            if isinstance(inner, list) and inner:
                return inner
    return []

def fetch_trending(limit=20):
    data = _call(get_trending_url(limit))
    if isinstance(data, list) and data:
        return data
    if isinstance(data, dict):
        for key in ["data", "results", "songs", "trending"]:
            inner = data.get(key)
            if isinstance(inner, list) and inner:
                return inner
    return []

# ── PAGE ROUTES ────────────────────────────────────────────────

@app.route('/')
@app.route('/home')
def home():
    raw_trending = fetch_trending(40)
    trending_songs = []
    if raw_trending:
        for item in raw_trending:
            norm = _normalize_song(item)
            if norm and norm.get("url"):
                trending_songs.append(norm)

    homepage_data = {
        "trending": trending_songs[:12],
        "charts": trending_songs[12:24] if len(trending_songs) > 12 else [],
        "new_releases": trending_songs[24:36] if len(trending_songs) > 24 else [],
        "personalized": False
    }

    selected_languages = session.get('selected_languages', ['hindi', 'english'])
    taste_summary = {
        'top_artists': [],
        'top_languages': [(l.title(), 1) for l in selected_languages],
        'top_genres': [],
        'top_moods': [('Chill', 1)],
        'metrics_collected': 0
    }

    return render_template(
        'home.html',
        data=homepage_data,
        taste=taste_summary,
        selected_languages=selected_languages
    )

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    songs = []
    if query:
        raw_results = fetch_songs(query, 30)
        for item in raw_results:
            norm = _normalize_song(item)
            if norm and norm.get("url"):
                songs.append(norm)
        # FIX: was db.save_search_query() which doesn't exist — correct name is add_to_search_history
        db.add_to_search_history(get_user_id(), query)
    return render_template('search.html', songs=songs, query=query, title="Search")

# ── PLAYER / CONTENT ROUTES ────────────────────────────────────

@app.route('/player/<song_id>')
def player(song_id):
    data = _call(get_song_url(song_id))
    song = _normalize_song(data) if data else None
    if not song:
        song = {
            "id": song_id, "title": "Unknown Song", "artist": "Unknown Artist",
            "album": "", "url": "", "image": "/static/images/default-album.png", "duration": 0,
        }
    if song.get("id"):
        db.add_to_recently_played(get_user_id(), {
            "song_id":   song.get("id"),
            "title":     song.get("title", "Unknown"),
            "artist":    song.get("artist", "Unknown"),
            "image_url": song.get("image", "")
        })
    return render_template('player.html', song=song, title=song.get("title", "Player"))

# ── API ROUTES ─────────────────────────────────────────────────

@app.route('/api/trending')
def api_trending():
    """
    FIX: This route was missing entirely — home.html JS and pullup-player.js
    both call /api/trending but it was never exposed as an endpoint.
    """
    limit = int(request.args.get('limit', 10))
    raw_trending = fetch_trending(limit)
    songs = []
    for item in raw_trending:
        norm = _normalize_song(item)
        if norm and norm.get("url"):
            songs.append(norm)
    return jsonify(songs)

@app.route('/api/search')
def api_search():
    """
    Search endpoint used by pullup-player.js queue/auto-extend feature
    and the Now Playing queue sheet.
    """
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 20))
    if not query:
        return jsonify([])
    raw_results = fetch_songs(query, limit)
    songs = []
    for item in raw_results:
        norm = _normalize_song(item)
        if norm and norm.get("url"):
            songs.append(norm)
    return jsonify(songs)

@app.route('/api/song/<song_id>')
def api_song(song_id):
    """
    Returns full song data for a given ID.
    Used by pullup-player.js when it needs to refetch a fresh audio URL.
    """
    data = _call(get_song_url(song_id))
    song = _normalize_song(data) if data else None
    if not song:
        return jsonify({"error": "Song not found"}), 404
    return jsonify(song)

@app.route('/api/similar-songs/<song_id>')
def api_similar_songs(song_id):
    """
    Returns songs similar to the given song_id.
    Used by player.html to show the 'More Like This' section.
    """
    limit = int(request.args.get('limit', 10))
    # Fetch the song first to get artist/title for search
    data = _call(get_song_url(song_id))
    song = _normalize_song(data) if data else None

    similar = []
    if song:
        artist = song.get("artist", "")
        primary_artist = artist.split(",")[0].strip() if artist else ""
        if primary_artist:
            raw = fetch_songs(primary_artist, limit + 5)
            for item in raw:
                norm = _normalize_song(item)
                # Exclude the current song itself
                if norm and norm.get("url") and norm.get("id") != song_id:
                    similar.append(norm)
                    if len(similar) >= limit:
                        break

    # Fallback to trending if nothing found
    if not similar:
        raw_trending = fetch_trending(limit)
        for item in raw_trending:
            norm = _normalize_song(item)
            if norm and norm.get("url") and norm.get("id") != song_id:
                similar.append(norm)
                if len(similar) >= limit:
                    break

    return jsonify(similar)

@app.route('/api/favorite', methods=['POST'])
def api_favorite():
    """Toggle a song in/out of the user's favorites."""
    data = request.get_json(silent=True) or {}
    user_id = get_user_id()
    song_data = {
        "id":       data.get("song_id", ""),
        "title":    data.get("title", "Unknown"),
        "artist":   data.get("artist", "Unknown"),
        "album":    data.get("album", ""),
        "duration": data.get("duration", 0),
        "image":    data.get("image_url", "/static/images/default-album.png"),
        "url":      data.get("audio_url", ""),
    }
    result = db.toggle_favorite(user_id, song_data)
    return jsonify(result)

@app.route('/api/favorites')
def api_favorites():
    """Return the user's favorite songs list."""
    user_id = get_user_id()
    favs = db.get_user_favorites(user_id)
    # Normalize keys so the JS player can read them
    normalized = []
    for f in favs:
        normalized.append({
            "song_id":   f.get("id", ""),
            "id":        f.get("id", ""),
            "title":     f.get("title", "Unknown"),
            "artist":    f.get("artist", "Unknown"),
            "album":     f.get("album", ""),
            "duration":  f.get("duration", 0),
            "image":     f.get("image", "/static/images/default-album.png"),
            "image_url": f.get("image", "/static/images/default-album.png"),
            "url":       f.get("url", ""),
            "audio_url": f.get("url", ""),
        })
    return jsonify(normalized)

@app.route('/api/artists')
def api_fallback_artists():
    return jsonify([])

@app.route('/api/suggestions')
def api_fallback_suggestions():
    raw_trending = fetch_trending(10)
    songs = []
    if raw_trending:
        for item in raw_trending:
            norm = _normalize_song(item)
            if norm and norm.get("url"):
                songs.append(norm)
    return jsonify(songs)

@app.route('/api/usuals')
def api_fallback_usuals():
    return jsonify([])

@app.route('/api/languages', methods=['POST'])
def save_languages():
    data = request.get_json(silent=True) or {}
    langs = data.get('languages', ['hindi'])
    session['selected_languages'] = [str(l).lower() for l in langs]
    return jsonify({"success": True})

@app.route('/api/debug')
def api_debug():
    try:
        r = requests.get(f"{API_BASE_URL}/", timeout=10)
        api_status = r.status_code
    except Exception as e:
        api_status = f"error: {e}"
    db_health = db.check_db_health()
    return jsonify({"api_base": API_BASE_URL, "api_status": api_status, "db_health": db_health})

# ── ERROR HANDLERS ─────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    empty_data = {"trending": [], "charts": [], "new_releases": [], "personalized": False}
    empty_taste = {'top_artists': [], 'top_languages': [], 'top_genres': [], 'top_moods': [], 'metrics_collected': 0}
    return render_template('home.html', data=empty_data, taste=empty_taste, selected_languages=[], title="Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

@app.route('/api/stats')
def api_stats():
    user_id = get_user_id()
    favs = db.get_user_favorites(user_id)
    history = db.get_recently_played(user_id)
    return jsonify({
        "total_favorites": len(favs),
        "total_plays": len(history),
        "total_playlists": 0,
        "listening_hours": 0
    })

# ── MAIN ───────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
        
