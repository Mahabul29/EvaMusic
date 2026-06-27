import os
import re
import requests
import uuid
import html as html_module
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, make_response

# ═══════════════════════════════════════════════════════════════
# CONFIG IMPORTS
# ═══════════════════════════════════════════════════════════════
from config import get_search_url, get_trending_url, get_song_url, API_BASE_URL

# ═══════════════════════════════════════════════════════════════
# OPTIONAL IMPORTS (graceful fallback if files missing)
# ═══════════════════════════════════════════════════════════════
try:
    from oauth import init_oauth, get_google_user, oauth, get_google_redirect_uri
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    init_oauth = get_google_user = oauth = get_google_redirect_uri = None

try:
    from language import register_lang_helpers, SUPPORTED_LANGUAGES
    I18N_AVAILABLE = True
except ImportError:
    I18N_AVAILABLE = False
    register_lang_helpers = SUPPORTED_LANGUAGES = None

try:
    import database as db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    db = None

try:
    from routes import profile_bp
    PROFILE_ROUTES_AVAILABLE = True
except ImportError:
    PROFILE_ROUTES_AVAILABLE = False
    profile_bp = None

# ═══════════════════════════════════════════════════════════════
# FLASK APP SETUP
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Trust proxy headers for HTTPS on Koyeb/Cloudflare
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-to-something-random-abc123_2026')

# Session cookies for HTTPS (Koyeb)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=60*60*24*365,
)

# i18n
if I18N_AVAILABLE and register_lang_helpers:
    register_lang_helpers(app)

# OAuth
if OAUTH_AVAILABLE and init_oauth:
    init_oauth(app)

# Blueprints
if PROFILE_ROUTES_AVAILABLE and profile_bp:
    app.register_blueprint(profile_bp)

# Database init
if DB_AVAILABLE and db and hasattr(db, 'init_db'):
    db.init_db()

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_user_id():
    """Return logged-in user's ID, or a guest ID."""
    if 'user_id' in session:
        return session['user_id']
    if 'guest_id' not in session:
        session['guest_id'] = str(uuid.uuid4())[:8]
    return session['guest_id']

def is_logged_in():
    return bool(session.get('logged_in'))

def _call(url, timeout=12):
    """Make GET request to music API."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] {url}: {e}")
    return None

def _extract_audio_url(data):
    """Extract audio URL from various API response shapes."""
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
    """Normalize a song object from any API response shape."""
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

    if isinstance(title, str): title = html_module.unescape(title)
    if isinstance(artist, str): artist = html_module.unescape(artist)
    if isinstance(album, str): album = html_module.unescape(album)

    return {
        "id": str(inner.get("id") or inner.get("song_id") or data.get("id") or ""),
        "title": title,
        "artist": artist,
        "album": album,
        "duration": int(inner.get("duration") or inner.get("length") or 0),
        "image": image or "/static/images/default-album.png",
        "url": audio_url,
    }

def fetch_songs(query, limit=20):
    """Search for songs."""
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
    """Fetch trending songs."""
    data = _call(get_trending_url(limit))
    if isinstance(data, list) and data:
        return data
    if isinstance(data, dict):
        for key in ["data", "results", "songs", "trending"]:
            inner = data.get(key)
            if isinstance(inner, list) and inner:
                return inner
    return []

def _build_homepage_data(raw_trending=None):
    """Build homepage data dict from trending songs."""
    if raw_trending is None:
        raw_trending = fetch_trending(40)
    trending_songs = []
    if raw_trending:
        for item in raw_trending:
            norm = _normalize_song(item)
            if norm and norm.get("url"):
                trending_songs.append(norm)

    return {
        "trending": trending_songs[:12],
        "charts": trending_songs[12:24] if len(trending_songs) > 12 else [],
        "new_releases": trending_songs[24:36] if len(trending_songs) > 24 else [],
        "personalized": False
    }

# ═══════════════════════════════════════════════════════════════
# LANGUAGE SWITCH
# ═══════════════════════════════════════════════════════════════

@app.route('/switch-language/<lang>')
def switch_language(lang):
    session.permanent = True
    lang = lang.lower().strip()
    if SUPPORTED_LANGUAGES and lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    session["lang"] = lang
    resp = make_response(redirect(request.referrer or url_for("home")))
    resp.set_cookie("evamusic_lang", lang, max_age=60*60*24*365)
    return resp

# ═══════════════════════════════════════════════════════════════
# PAGE ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
@app.route('/home')
def home():
    homepage_data = _build_homepage_data()
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
        if DB_AVAILABLE and db and hasattr(db, 'add_to_search_history'):
            db.add_to_search_history(get_user_id(), query)
    return render_template('search.html', songs=songs, query=query, title="Search")

@app.route('/player/<song_id>')
def player(song_id):
    data = _call(get_song_url(song_id))
    song = _normalize_song(data) if data else None
    if not song:
        song = {
            "id": song_id, "title": "Unknown Song", "artist": "Unknown Artist",
            "album": "", "url": "", "image": "/static/images/default-album.png", "duration": 0,
        }
    if song.get("id") and DB_AVAILABLE and db and hasattr(db, 'add_to_recently_played'):
        db.add_to_recently_played(get_user_id(), {
            "song_id": song.get("id"),
            "title": song.get("title", "Unknown"),
            "artist": song.get("artist", "Unknown"),
            "image_url": song.get("image", "")
        })
    return render_template('player.html', song=song, title=song.get("title", "Player"))

# ═══════════════════════════════════════════════════════════════
# DESKTOP VIEW
# ═══════════════════════════════════════════════════════════════

@app.route('/desktop')
def desktop():
    return render_template('windows.html')

# ═══════════════════════════════════════════════════════════════
# AUTH / OAUTH ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/login/google')
def login_google():
    if not OAUTH_AVAILABLE or not oauth:
        return redirect('/?error=oauth_not_configured')
    redirect_uri = get_google_redirect_uri()
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def authorize_google():
    if not OAUTH_AVAILABLE or not oauth:
        return redirect('/?error=oauth_not_configured')
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        print(f"[OAuth Error] {e}")
        return redirect('/?error=oauth_failed')

    user_info = get_google_user(token) if get_google_user else None
    if not user_info:
        return redirect('/?error=oauth_failed')

    email = user_info.get('email')
    name = user_info.get('name', email.split('@')[0] if email else 'User')
    picture = user_info.get('picture', '')

    user_id = None
    if DB_AVAILABLE and db and hasattr(db, '_load'):
        users = db._load("users")
        for uid, udata in users.items():
            if udata.get('email') == email:
                user_id = uid
                break

        if not user_id:
            user_id = str(uuid.uuid4())[:8]
            users[user_id] = {
                "id": user_id,
                "email": email,
                "name": name,
                "display_name": name,
                "username": email.split('@')[0] if email else f"user_{user_id}",
                "picture": picture,
                "provider": "google",
                "bio": "Music lover",
                "social_links": {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            db._save("users", users)
    else:
        # Fallback without database
        user_id = str(uuid.uuid4())[:8]

    session['user_id'] = user_id
    session['logged_in'] = True
    session['user_name'] = name
    session['user_email'] = email
    session['user_picture'] = picture
    session.permanent = True

    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/me')
def api_me():
    """Return current logged-in user info."""
    if not session.get('logged_in'):
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in": True,
        "user_id": session.get('user_id'),
        "name": session.get('user_name'),
        "email": session.get('user_email'),
        "picture": session.get('user_picture')
    })

# ═══════════════════════════════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/api/trending')
def api_trending():
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
    data = _call(get_song_url(song_id))
    song = _normalize_song(data) if data else None
    if not song:
        return jsonify({"error": "Song not found"}), 404
    return jsonify(song)

@app.route('/api/similar-songs/<song_id>')
def api_similar_songs(song_id):
    limit = int(request.args.get('limit', 10))
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
                if norm and norm.get("url") and norm.get("id") != song_id:
                    similar.append(norm)
                if len(similar) >= limit:
                    break

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
    data = request.get_json(silent=True) or {}
    user_id = get_user_id()
    song_data = {
        "id": data.get("song_id", ""),
        "title": data.get("title", "Unknown"),
        "artist": data.get("artist", "Unknown"),
        "album": data.get("album", ""),
        "duration": data.get("duration", 0),
        "image": data.get("image_url", "/static/images/default-album.png"),
        "url": data.get("audio_url", ""),
    }
    if DB_AVAILABLE and db and hasattr(db, 'toggle_favorite'):
        result = db.toggle_favorite(user_id, song_data)
    else:
        result = {"success": True, "action": "added"}
    return jsonify(result)

@app.route('/api/favorites')
def api_favorites():
    user_id = get_user_id()
    if DB_AVAILABLE and db and hasattr(db, 'get_user_favorites'):
        favs = db.get_user_favorites(user_id)
    else:
        favs = []
    normalized = []
    for f in favs:
        normalized.append({
            "song_id": f.get("id", ""),
            "id": f.get("id", ""),
            "title": f.get("title", "Unknown"),
            "artist": f.get("artist", "Unknown"),
            "album": f.get("album", ""),
            "duration": f.get("duration", 0),
            "image": f.get("image", "/static/images/default-album.png"),
            "image_url": f.get("image", "/static/images/default-album.png"),
            "url": f.get("url", ""),
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
    db_health = db.check_db_health() if DB_AVAILABLE and db and hasattr(db, 'check_db_health') else "unknown"
    return jsonify({"api_base": API_BASE_URL, "api_status": api_status, "db_health": db_health})

@app.route('/api/stats')
def api_stats():
    user_id = get_user_id()
    favs = db.get_user_favorites(user_id) if DB_AVAILABLE and db and hasattr(db, 'get_user_favorites') else []
    history = db.get_recently_played(user_id) if DB_AVAILABLE and db and hasattr(db, 'get_recently_played') else []
    return jsonify({
        "total_favorites": len(favs),
        "total_plays": len(history),
        "total_playlists": 0,
        "listening_hours": 0
    })

# ═══════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    empty_data = {"trending": [], "charts": [], "new_releases": [], "personalized": False}
    empty_taste = {'top_artists': [], 'top_languages': [], 'top_genres': [], 'top_moods': [], 'metrics_collected': 0}
    return render_template('home.html', data=empty_data, taste=empty_taste, selected_languages=[], title="Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
