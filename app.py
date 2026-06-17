import os
import requests
import uuid
import re
from flask import Flask, render_template, jsonify, request, send_from_directory, session
from config import get_search_url, get_trending_url, get_song_url, API_BASE_URL

import database as db

# ── Extension Modules ──────────────────────────────────────────
from suggest import build_homepage_sections, get_suggestions_for_user
from refresh import refresh_bp
from user.trackuser import on_song_liked, get_full_taste_summary

app = Flask(__name__)

# Fallback development key if environment variable isn't injected
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-to-something-random-abc123_2026')

# Register the smart-queue blueprint
app.register_blueprint(refresh_bp)

db.init_db()

_LAST_GOOD_TRENDING = []
_LAST_GOOD_TRENDING_LANG = {}  # cache per language
_LAST_TRENDING_FETCH_TIME = 0  # timestamp for cache expiry

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# ═══════════════════════════════════════════════════════════════
# LANGUAGE DETECTION & FILTERING
# ═══════════════════════════════════════════════════════════════

LANG_INDICATORS = {
    'hindi':     ['hindi', 'bollywood', 'hindi mix', 'हिंदी'],
    'english':   ['english', 'pop', 'rock', 'edm', 'hip-hop', 'rap', 'r&b'],
    'punjabi':   ['punjabi', 'bhangra', 'ਪੰਜਾਬੀ'],
    'tamil':     ['tamil', 'kollywood', 'தமிழ்'],
    'telugu':    ['telugu', 'tollywood', 'తెలుగు'],
    'marathi':   ['marathi', 'मराठी'],
    'gujarati':  ['gujarati', 'ગુજરાતી'],
    'bengali':   ['bengali', 'bangla', 'বাংলা'],
    'kannada':   ['kannada', 'sandalwood', 'ಕನ್ನಡ'],
    'malayalam': ['malayalam', 'mollywood', 'മലയാളം'],
    'urdu':      ['urdu', 'ghazal', 'qawwali', 'اردو'],
}

ARTIST_LANG_MAP = {
    'arijit singh': 'hindi', 'shreya ghoshal': 'hindi', 'sonu nigam': 'hindi',
    'jubin nautiyal': 'hindi', 'neha kakkar': 'hindi', 'atif aslam': 'hindi',
    'armaan malik': 'hindi', 'vishal mishra': 'hindi', 'pritam': 'hindi',
    'a.r. rahman': 'hindi', 'shankar ehsaan loy': 'hindi', 'badshah': 'hindi',
    'guru randhawa': 'hindi', 'jass manak': 'hindi', 'darshan raval': 'hindi',
    'tony kakkar': 'hindi', 'javed ali': 'hindi', 'mohit chauhan': 'hindi',
    'kk': 'hindi', 'kumar sanu': 'hindi', 'udit narayan': 'hindi',
    'alka yagnik': 'hindi', 'sunidhi chauhan': 'hindi', 'shreya': 'hindi',
    'arijit': 'hindi', 'jubin': 'hindi', 'neha': 'hindi',
    'kishore kumar': 'hindi', 'lata mangeshkar': 'hindi', 'asha bhosle': 'hindi',
    'rahat fateh ali khan': 'hindi', 'ankur r pathakk': 'hindi',
    'raghav chaitanya': 'hindi', 'hansraj raghuwanshi': 'hindi',
    'vishal dadlani': 'hindi', 'shekhar ravjiani': 'hindi',
    'diljit dosanjh': 'punjabi', 'sidhu moose wala': 'punjabi',
    'karan aujla': 'punjabi', 'ap dhillon': 'punjabi', 'shubh': 'punjabi',
    'jasmine sandlas': 'punjabi', 'amrinder gill': 'punjabi',
    'babbu maan': 'punjabi', 'gippy grewal': 'punjabi',
    'jassie gill': 'punjabi', 'mankirt aulakh': 'punjabi',
    'nimrat khaira': 'punjabi', 'akhil': 'punjabi',
    'jind universe': 'punjabi', 'wavy': 'punjabi',
    'taylor swift': 'english', 'ed sheeran': 'english', 'drake': 'english',
    'the weeknd': 'english', 'ariana grande': 'english', 'justin bieber': 'english',
    'billie eilish': 'english', 'dua lipa': 'english', 'bruno mars': 'english',
    'coldplay': 'english', 'imagine dragons': 'english', 'maroon 5': 'english',
    'post malone': 'english', 'travis scott': 'english', 'eminem': 'english',
    'rihanna': 'english', 'beyoncé': 'english', 'sia': 'english',
    'anirudh ravichander': 'tamil', 'a.r. rahman': 'tamil', 'yuvan shankar raja': 'tamil',
    'g.v. prakash kumar': 'tamil', 'hiphop tamizha': 'tamil',
    'santhosh narayanan': 'tamil', 'd. imman': 'tamil',
    's. thaman': 'telugu', 'devi sri prasad': 'telugu',
    'anirudh': 'telugu', 'mickey j meyer': 'telugu',
    'arijit singh': 'bengali', 'anupam roy': 'bengali',
    'jeet gannguli': 'bengali', 'shreya ghoshal': 'bengali',
    'ajay-atul': 'marathi', 'avdhoot gupte': 'marathi',
    'nusrat fateh ali khan': 'urdu', 'rahat fateh ali khan': 'urdu',
    'atif aslam': 'urdu', 'ali zafar': 'urdu',
}

def _detect_song_language(song):
    artist = (song.get('artist') or song.get('primaryArtists') or song.get('singers') or '').lower()
    for artist_name, lang in ARTIST_LANG_MAP.items():
        if artist_name in artist or artist in artist_name:
            return lang

    title = (song.get('title') or song.get('name') or '').lower()
    for lang, indicators in LANG_INDICATORS.items():
        for indicator in indicators:
            if indicator in title or indicator in artist:
                return lang

    album = (song.get('album') or '').lower()
    for lang, indicators in LANG_INDICATORS.items():
        for indicator in indicators:
            if indicator in album:
                return lang

    lang_field = (song.get('language') or '').lower()
    if lang_field and lang_field in LANG_INDICATORS:
        return lang_field

    return 'hindi'

# ═══════════════════════════════════════════════════════════════
# CORE HELPERS
# ═══════════════════════════════════════════════════════════════

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def _call(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=7)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] Failed to fetch url {url}: {e}")
    return None

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

    URL_KEYS = ["url", "downloadUrl", "download_url", "media_url", "audio_url", "stream_url", "song_url", "link"]
    audio_url = ""
    for key in URL_KEYS:
        val = inner.get(key)
        if val:
            if isinstance(val, list) and val:
                entry = val[-1]
                if isinstance(entry, dict):
                    audio_url = entry.get("url") or entry.get("link") or ""
                elif isinstance(entry, str):
                    audio_url = entry
            elif isinstance(val, str) and val.startswith("http"):
                audio_url = val
        if audio_url:
            break

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
        "url":      audio_url,
    }

def fetch_trending(limit=30, language='All'):
    import time
    global _LAST_GOOD_TRENDING, _LAST_GOOD_TRENDING_LANG, _LAST_TRENDING_FETCH_TIME

    now = time.time()
    cache_duration = 600  # 10 minutes cache window

    # Check language specific cache validity
    if language != 'All' and language in _LAST_GOOD_TRENDING_LANG and (now - _LAST_TRENDING_FETCH_TIME < cache_duration):
        return _LAST_GOOD_TRENDING_LANG[language][:limit]
    elif language == 'All' and _LAST_GOOD_TRENDING and (now - _LAST_TRENDING_FETCH_TIME < cache_duration):
        return _LAST_GOOD_TRENDING[:limit]

    # Pull remote data asset
    raw = _call(get_trending_url())
    if not raw:
        if language != 'All':
            return _LAST_GOOD_TRENDING_LANG.get(language, _LAST_GOOD_TRENDING)[:limit]
        return _LAST_GOOD_TRENDING[:limit]

    items = []
    if isinstance(raw, dict):
        items = raw.get("data") or raw.get("results") or []
    elif isinstance(raw, list):
        items = raw

    normalized_list = []
    lang_buckets = {l: [] for l in LANG_INDICATORS}

    for item in items:
        norm = _normalize_song(item)
        if norm and norm.get("url"):
            normalized_list.append(norm)
            detected_l = _detect_song_language(norm)
            if detected_l in lang_buckets:
                lang_buckets[detected_l].append(norm)

    if normalized_list:
        _LAST_GOOD_TRENDING = normalized_list
        _LAST_TRENDING_FETCH_TIME = now
        for lang, b_items in lang_buckets.items():
            _LAST_GOOD_TRENDING_LANG[lang] = b_items

    if language != 'All':
        return _LAST_GOOD_TRENDING_LANG.get(language.lower(), [])[:limit]
    return _LAST_GOOD_TRENDING[:limit]

def fetch_songs(query, limit=20):
    if not query:
        return []
    raw = _call(get_search_url(query))
    if not raw:
        return []
    
    items = []
    if isinstance(raw, dict):
        items = raw.get("data") or raw.get("results") or raw.get("data", {}).get("results") or []
    elif isinstance(raw, list):
        items = raw

    results = []
    for item in items:
        norm = _normalize_song(item)
        if norm and norm.get("url"):
            results.append(norm)
    return results[:limit]

# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    user_id = get_user_id()
    lang = request.args.get('lang', 'All')
    trending = fetch_trending(30, lang)
    return render_template('index.html', songs=trending, title="Trending Mix", selected_lang=lang)

@app.route('/home')
def home():
    user_id = get_user_id()
    lang = request.args.get('lang', 'All')
    
    # 1. Defensively handle baseline music pools
    try:
        trending = fetch_trending(40, lang)
    except Exception as e:
        print(f"[home] Critical Trending API collection break: {e}")
        trending = []

    # 2. Defensively handle suggestions and circular execution metrics
    try:
        # Avoid structural deadlocks by passing fetch_songs as an operation reference
        sections = build_homepage_sections(user_id, trending, fetch_songs)
        taste = get_full_taste_summary(user_id)
    except Exception as e:
        import traceback
        print(f"[home] Recommendation tracking breakdown intercepted:\n{traceback.format_exc()}")
        sections = {}
        taste = {}

    return render_template(
        'home.html',
        title="Your Daily Mix",
        songs=sections.get("for_you") or trending[:20],
        sections=sections,
        taste=taste,
        selected_lang=lang,
    )

@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    songs = fetch_songs(q, 25) if q else []
    if q and songs:
        db.add_to_search_history(get_user_id(), q)
    return render_template('index.html', songs=songs, title=f"Results for '{q}'" if q else "Search")

@app.route('/song/<song_id>')
def view_song(song_id):
    raw = _call(get_song_url(song_id))
    norm = _normalize_song(raw) if raw else None
    if not norm or not norm.get("url"):
        return render_template('index.html', songs=[], error="Song not found or unplayable.")
    return render_template('index.html', songs=[norm], title=norm['title'])

# ── API ENDPOINTS ──────────────────────────────────────────────

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    return jsonify(fetch_songs(q, 20))

@app.route('/api/trending')
def api_trending():
    lang = request.args.get('lang', 'All')
    return jsonify(fetch_trending(20, lang))

@app.route('/api/favorites', methods=['GET', 'POST'])
def api_favorites():
    user_id = get_user_id()
    if request.method == 'POST':
        song_data = request.json
        if not song_data or not song_data.get('id'):
            return jsonify({"error": "Missing song data"}), 400
        
        success = db.add_to_favorites(user_id, song_data)
        if success:
            on_song_liked(user_id, song_data)
        return jsonify({"success": success})
    
    return jsonify(db.get_user_favorites(user_id))

@app.route('/api/favorites/toggle', methods=['POST'])
def api_favorites_toggle():
    user_id = get_user_id()
    song_data = request.json
    if not song_data or not song_data.get('id'):
        return jsonify({"error": "Missing song data"}), 400
    
    result = db.toggle_favorite(user_id, song_data)
    return jsonify(result)

@app.route('/api/favorites/check/<song_id>')
def api_check_favorite(song_id):
    is_fav = db.is_favorite(get_user_id(), song_id)
    return jsonify({"is_favorite": is_fav})

@app.route('/api/history', methods=['GET', 'POST'])
def api_history():
    user_id = get_user_id()
    if request.method == 'POST':
        song_data = request.json
        if not song_data or not song_data.get('id'):
            return jsonify({"error": "Missing item data"}), 400
        db.add_to_history(user_id, song_data)
        return jsonify({"success": True})
    return jsonify(db.get_recently_played(user_id, 30))

@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    db.clear_history(get_user_id())
    return jsonify({"success": True})

@app.route('/api/recommendations')
def api_recommendations():
    user_id = get_user_id()
    trending = fetch_trending(40)
    suggestions = get_suggestions_for_user(user_id, trending, limit=15)
    return jsonify(suggestions)

@app.route('/api/debug')
def api_debug():
    try:
        r = requests.get(f"{API_BASE_URL}/", timeout=10)
        api_status = r.status_code
    except Exception as e:
        api_status = f"error: {e}"
    db_health = db.check_db_health()
    return jsonify({"api_base": API_BASE_URL, "api_status": api_status, "db_health": db_health})

@app.route('/api/debug/song/<song_id>')
def api_debug_song(song_id):
    raw  = _call(get_song_url(song_id))
    norm = _normalize_song(raw) if raw else None
    return jsonify({
        "raw":             raw,
        "normalized":      norm,
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
    err_msg = traceback.format_exc()
    print(f"[500 CRITICAL ERROR]\n{err_msg}")
    # Render visible diagnostic message instead of standard silent JSON strings
    return f"<h3>Internal Server Error (500)</h3><pre>{err_msg}</pre>", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
