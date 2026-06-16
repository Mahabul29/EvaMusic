import os
import requests
import uuid
import re
from flask import Flask, render_template, jsonify, request, send_from_directory, session
from config import get_search_url, get_trending_url, get_song_url, API_BASE_URL

import database as db

# ── New modules ────────────────────────────────────────────────
from suggest import build_homepage_sections, get_suggestions_for_user
from refresh import refresh_bp
from user.trackuser import on_song_liked, get_full_taste_summary

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

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

# Language indicators in song metadata
LANG_INDICATORS = {
    'hindi':     ['hindi', 'bollywood', 'हिंदी'],
    'english':   ['english', 'pop', 'rock', 'edm', 'hip-hop', 'r&b'],
    'punjabi':   ['punjabi', 'bhangra', 'ਪੰਜਾਬੀ'],
    'tamil':     ['tamil', 'kollywood', 'தமிழ்'],
    'telugu':    ['telugu', 'tollywood', 'తెలుగు'],
    'marathi':   ['marathi', 'मराठी'],
    'gujarati':  ['gujarati', 'ગુજરાતી'],
    'bengali':   ['bengali', 'bangla', 'বাংলা'],
    'kannada':   ['kannada', 'sandalwood', 'ಕನ್ನಡ'],
    'malayalam': ['malayalam', 'mollywood', 'മലയാളം'],
    'urdu':      ['urdu', 'اردو', 'ghazal', 'qawwali'],
}

# Artist → Language mapping (common knowledge)
ARTIST_LANG_MAP = {
    # Hindi
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

    # Punjabi
    'diljit dosanjh': 'punjabi', 'sidhu moose wala': 'punjabi',
    'karan aujla': 'punjabi', 'ap dhillon': 'punjabi', 'shubh': 'punjabi',
    'jasmine sandlas': 'punjabi', 'amrinder gill': 'punjabi',
    'babbu maan': 'punjabi', 'gippy grewal': 'punjabi',
    'jassie gill': 'punjabi', 'mankirt aulakh': 'punjabi',
    'nimrat khaira': 'punjabi', 'akhil': 'punjabi',
    'jind universe': 'punjabi', 'wavy': 'punjabi',

    # English
    'taylor swift': 'english', 'ed sheeran': 'english', 'drake': 'english',
    'the weeknd': 'english', 'ariana grande': 'english', 'justin bieber': 'english',
    'billie eilish': 'english', 'dua lipa': 'english', 'bruno mars': 'english',
    'coldplay': 'english', 'imagine dragons': 'english', 'maroon 5': 'english',
    'post malone': 'english', 'travis scott': 'english', 'eminem': 'english',
    'rihanna': 'english', 'beyoncé': 'english', 'sia': 'english',

    # Tamil
    'anirudh ravichander': 'tamil', 'a.r. rahman': 'tamil', 'yuvan shankar raja': 'tamil',
    'g.v. prakash kumar': 'tamil', 'hiphop tamizha': 'tamil',
    'santhosh narayanan': 'tamil', 'd. imman': 'tamil',

    # Telugu
    's. thaman': 'telugu', 'devi sri prasad': 'telugu',
    'anirudh': 'telugu', 'mickey j meyer': 'telugu',

    # Bengali
    'arijit singh': 'bengali', 'anupam roy': 'bengali',
    'jeet gannguli': 'bengali', 'shreya ghoshal': 'bengali',

    # Marathi
    'ajay-atul': 'marathi', 'avdhoot gupte': 'marathi',

    # Urdu
    'nusrat fateh ali khan': 'urdu', 'rahat fateh ali khan': 'urdu',
    'atif aslam': 'urdu', 'ali zafar': 'urdu',
}


def _detect_song_language(song):
    """Detect language of a song from its metadata."""
    # Check artist name
    artist = (song.get('artist') or song.get('primaryArtists') or song.get('singers') or '').lower()
    for artist_name, lang in ARTIST_LANG_MAP.items():
        if artist_name in artist or artist in artist_name:
            return lang

    # Check song title for language clues
    title = (song.get('title') or song.get('name') or '').lower()
    for lang, indicators in LANG_INDICATORS.items():
        for indicator in indicators:
            if indicator in title or indicator in artist:
                return lang

    # Check album name
    album = (song.get('album') or '').lower()
    for lang, indicators in LANG_INDICATORS.items():
        for indicator in indicators:
            if indicator in album:
                return lang

    # Check language field if present
    lang_field = (song.get('language') or '').lower()
    if lang_field and lang_field in LANG_INDICATORS:
        return lang_field

    # Default to hindi for Indian music platform
    return 'hindi'


def _filter_by_language(songs, lang):
    """Filter songs by language. Returns all if lang is 'all' or None."""
    if not lang or lang.lower() == 'all':
        return songs

    lang = lang.lower()
    filtered = []
    for song in songs:
        detected = _detect_song_language(song)
        if detected == lang:
            filtered.append(song)

    # If too few results, pad with unclassified songs
    if len(filtered) < 5 and len(songs) > len(filtered):
        seen_ids = {s.get('id') or s.get('song_id') for s in filtered}
        for song in songs:
            sid = song.get('id') or song.get('song_id')
            if sid not in seen_ids:
                filtered.append(song)
            if len(filtered) >= 20:
                break

    return filtered


def _extract_artists_from_songs(songs, lang=None):
    """Extract unique artists from songs, optionally filtered by language."""
    artists = []
    seen = set()

    for song in songs:
        artist_raw = song.get('artist') or song.get('primaryArtists') or song.get('singers') or ''
        artist_names = [a.strip() for a in re.split(r'[,/&]', artist_raw) if a.strip()]

        for name in artist_names:
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)

            # Detect language
            detected_lang = None
            for a_name, a_lang in ARTIST_LANG_MAP.items():
                if a_name in key or key in a_name:
                    detected_lang = a_lang
                    break

            # Filter by language if specified
            if lang and lang.lower() != 'all':
                if detected_lang and detected_lang != lang.lower():
                    continue

            img = song.get('image') or song.get('image_url') or song.get('thumbnail') or ''
            if isinstance(img, list) and img:
                img = img[-1].get('url') if isinstance(img[-1], dict) else img[-1]

            artists.append({
                'id': key.replace(' ', '_'),
                'name': name,
                'image': img or '/static/images/default-album.png',
                'language': detected_lang or 'hindi',
                'genre': song.get('genre') or 'Trending'
            })

    return artists


# ── Helpers ────────────────────────────────────────────────────

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        db.create_user(session['user_id'], f"User_{session['user_id'][:8]}")
    return session['user_id']

def is_logged_in():
    return bool(session.get('logged_in'))

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

    return {
        "id":       inner.get("id") or inner.get("song_id") or data.get("id") or "",
        "title":    inner.get("title") or inner.get("name") or inner.get("song") or "Unknown",
        "artist":   inner.get("artist") or inner.get("primaryArtists") or inner.get("singers") or "Unknown",
        "album":    inner.get("album") or inner.get("album_name") or "",
        "duration": inner.get("duration") or inner.get("length") or 0,
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

def fetch_trending(limit=20, lang=None):
    """Fetch trending songs, optionally filtered by language.
    ALWAYS tries API first, only falls back to cache if API fails."""
    global _LAST_GOOD_TRENDING, _LAST_GOOD_TRENDING_LANG

    # Try API first — always
    try:
        data = _call(get_trending_url(limit * 3))  # fetch more to filter
        songs = []
        if isinstance(data, list) and data:
            songs = data
        if isinstance(data, dict):
            for key in ["data", "results", "songs"]:
                inner = data.get(key)
                if isinstance(inner, list) and inner:
                    songs = inner
                    break

        # If API returned songs, use them and update cache
        if songs:
            print(f"[fetch_trending] API returned {len(songs)} songs")
            _LAST_GOOD_TRENDING = songs

            # Filter by language if specified
            if lang and lang.lower() != 'all':
                songs = _filter_by_language(songs, lang)

            _LAST_GOOD_TRENDING_LANG[lang or 'all'] = songs
            return songs[:limit]
        else:
            print("[fetch_trending] API returned empty, will try fallback")
    except Exception as e:
        print(f"[fetch_trending] API call failed: {e}")

    # Fallback to cache if API failed
    cache_key = lang or 'all'
    if cache_key in _LAST_GOOD_TRENDING_LANG:
        cached = _LAST_GOOD_TRENDING_LANG[cache_key]
        if cached:
            print(f"[fetch_trending] Using cached songs for lang={cache_key}")
            return cached[:limit]

    if _LAST_GOOD_TRENDING:
        print("[fetch_trending] Using last good trending fallback")
        filtered = _filter_by_language(_LAST_GOOD_TRENDING, lang)
        return filtered[:limit]

    print("[fetch_trending] No songs available at all")
    return []

def fetch_song(song_id):
    data = _call(get_song_url(song_id))
    if not data:
        return None
    song = _normalize_song(data)
    if not song:
        return None
    if not song["url"]:
        print(f"[fetch_song] WARNING: No audio URL for {song_id}")
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
    return render_template('index.html', songs=songs, title="Home")


@app.route('/home')
def home():
    """
    Smart homepage: personalised sections based on taste profile.
    Falls back to trending for new users.
    """
    user_id       = get_user_id()

    # Get user's preferred language from query param or default to All
    lang = request.args.get('lang', 'All')

    trending      = fetch_trending(40, lang)   # fetch a large pool to rank from

    # Build personalised sections (suggest.py)
    sections = build_homepage_sections(user_id, trending)

    # Taste summary for the template (top artists, genres, etc.)
    taste = get_full_taste_summary(user_id)

    return render_template(
        'home.html',
        title="Your Daily Mix",
        # Legacy: pass songs so old template still works
        songs=sections.get("for_you") or trending[:20],
        # New: all smart sections
        sections=sections,
        taste=taste,
        selected_lang=lang,
    )


@app.route('/search')
def search():
    query = request.args.get('q', '')
    lang = request.args.get('lang', 'All')
    songs = []
    if query:
        raw = fetch_songs(query, 30)
        # Filter by language
        if lang and lang.lower() != 'all':
            raw = _filter_by_language(raw, lang)
        # Re-rank results by user preference
        songs = get_suggestions_for_user(get_user_id(), raw, limit=30)
        db.save_search_query(get_user_id(), query)
    return render_template('search.html', songs=songs, query=query, title="Search")


@app.route('/trending')
def trending():
    lang = request.args.get('lang', 'All')
    songs = fetch_trending(24, lang)
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

@app.route('/help')
def help_support():
    return render_template('help.html', title="Help & Support")


# ── PLAYER / CONTENT ROUTES ────────────────────────────────────

@app.route('/player/<song_id>')
def player(song_id):
    song = fetch_song(song_id)
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
        # Also update taste profile on play
        try:
            from user.trackuser import on_song_played
            on_song_played(get_user_id(), song)
        except Exception as e:
            print(f"[PLAYER] Taste tracking error: {e}")
    return render_template('player.html', song=song, title=song.get("title", "Player"))

@app.route('/playlist/<playlist_id>')
def playlist(playlist_id):
    songs = fetch_playlist_songs(playlist_id)
    return render_template('playlist.html', songs=songs, title="Playlist")

@app.route('/album/<album_id>')
def album(album_id):
    songs = fetch_album_songs(album_id)
    return render_template('album.html', songs=songs, title="Album")

@app.route('/artist/<artist_name>')
def artist(artist_name):
    from urllib.parse import unquote
    name = unquote(artist_name)

    raw_songs = fetch_songs(name, 30)
    songs = [_normalize_song(s) for s in raw_songs]
    songs = [s for s in songs if s]

    name_lower = name.lower()
    filtered = [s for s in songs if name_lower in str(s.get('artist', '')).lower()]
    if filtered:
        songs = filtered

    return render_template('artist.html', songs=songs, title=name)


# ── AUTH ROUTES ────────────────────────────────────────────────

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    user_id = get_user_id()
    result = db.create_account(user_id, username, password)

    if result.get('success'):
        session['logged_in'] = True
        session['username'] = result['username']
        session['user_id'] = result['user_id']

    return jsonify(result)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    result = db.verify_login(username, password)

    if result.get('success'):
        guest_user_id  = session.get('user_id')
        target_user_id = result['user_id']

        if guest_user_id and guest_user_id != target_user_id:
            db.merge_guest_data(guest_user_id, target_user_id)

        session['user_id']   = target_user_id
        session['username']  = result['username']
        session['logged_in'] = True

    return jsonify(result)

@app.route('/api/logout', methods=['POST'])
def api_logout():
    from refresh import clear_session_skips
    clear_session_skips()
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)
    return jsonify({"success": True, "message": "Logged out"})

@app.route('/api/auth-status')
def api_auth_status():
    if is_logged_in():
        return jsonify({"logged_in": True, "username": session.get('username')})
    return jsonify({"logged_in": False})

@app.route('/api/change-password', methods=['POST'])
def api_change_password():
    if not is_logged_in():
        return jsonify({"success": False, "message": "You must be logged in"}), 401

    data = request.get_json(silent=True) or request.form
    old_password     = data.get('old_password') or ''
    new_password     = data.get('new_password') or ''
    confirm_password = data.get('confirm_password') or ''

    if new_password != confirm_password:
        return jsonify({"success": False, "message": "New passwords do not match"})

    result = db.change_password(session['user_id'], old_password, new_password)
    return jsonify(result)


# ── PROFILE ROUTES ─────────────────────────────────────────────

@app.route('/profile')
def profile():
    try:
        user_id   = get_user_id()
        favorites = db.get_user_favorites(user_id)
        playlists = db.get_user_playlists(user_id)
        recent    = db.get_recently_played(user_id, 5)
        all_plays = db.get_recently_played(user_id, 9999)

        # Taste insights for profile page
        taste = get_full_taste_summary(user_id)

        stats = {
            "total_favorites": len(favorites),
            "total_playlists": len(playlists),
            "total_plays":     len(all_plays),
            "listening_hours": round(len(all_plays) * 3.5 / 60, 1)
        }

        user_doc = {}
        try:
            coll = db.get_collection("users")
            if coll is not None:
                result = coll.find_one({"user_id": user_id})
                if isinstance(result, dict):
                    user_doc = result
        except Exception as e:
            print(f"[PROFILE] Error fetching user doc: {e}")

        raw_social = user_doc.get("social_links")
        if not isinstance(raw_social, dict):
            raw_social = {}

        profile_data = {
            "username":     user_doc.get("username") or "EvaUser",
            "display_name": user_doc.get("display_name") or user_doc.get("username") or "EvaUser",
            "bio":          user_doc.get("bio") or "Music lover 🎵",
            "avatar_url":   user_doc.get("avatar_url") or "av1",
            "social_links": {
                "instagram": raw_social.get("instagram", ""),
                "twitter":   raw_social.get("twitter", ""),
                "youtube":   raw_social.get("youtube", ""),
                "spotify":   raw_social.get("spotify", ""),
            }
        }

        return render_template('profile.html',
                               title="Profile",
                               profile=profile_data,
                               stats=stats,
                               taste=taste,
                               recently_played=recent,
                               favorites=favorites[:5],
                               playlists=playlists[:5])
    except Exception as e:
        import traceback
        print(f"[PROFILE ERROR] {e}")
        print(traceback.format_exc())
        return render_template('profile.html',
                               title="Profile",
                               profile={
                                   "username": "EvaUser",
                                   "display_name": "EvaUser",
                                   "bio": "Music lover 🎵",
                                   "avatar_url": "av1",
                                   "social_links": {"instagram": "", "twitter": "", "youtube": "", "spotify": ""}
                               },
                               stats={"total_favorites": 0, "total_playlists": 0, "total_plays": 0, "listening_hours": 0},
                               taste={},
                               recently_played=[],
                               favorites=[],
                               playlists=[]), 500


@app.route('/profile/edit')
def edit_profile():
    user_id  = get_user_id()
    user_doc = {}
    try:
        coll = db.get_collection("users")
        if coll is not None:
            result = coll.find_one({"user_id": user_id})
            if isinstance(result, dict):
                user_doc = result
    except Exception as e:
        print(f"[EDIT_PROFILE] DB error: {e}")

    profile_data = {
        "username":     user_doc.get("username") or "EvaUser",
        "display_name": user_doc.get("display_name") or user_doc.get("username") or "EvaUser",
        "bio":          user_doc.get("bio") or "Music lover 🎵",
        "avatar_url":   user_doc.get("avatar_url") or "av1",
    }

    avatars = [f"/static/images/avatars/avatar{i}.png" for i in range(1, 9)]

    return render_template('edit_profile.html',
                           title="Edit Profile",
                           profile=profile_data,
                           avatars=avatars)


@app.route('/favorites')
def favorites():
    user_id = get_user_id()
    songs   = db.get_user_favorites(user_id)
    return render_template('favorites.html', songs=songs, title="My Favorites")

@app.route('/history')
def history():
    user_id = get_user_id()
    songs   = db.get_recently_played(user_id, 50)
    return render_template('history.html', songs=songs, title="Listening History")

@app.route('/playlists')
def playlists():
    user_id       = get_user_id()
    playlists_data = db.get_user_playlists(user_id)
    return render_template('playlists.html', playlists=playlists_data, title="My Playlists")


# ── API ROUTES ─────────────────────────────────────────────────

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    lang = request.args.get('lang', 'All')
    songs = fetch_songs(query, limit)
    if lang and lang.lower() != 'all':
        songs = _filter_by_language(songs, lang)
    return jsonify(songs)

@app.route('/api/trending')
def api_trending():
    limit = request.args.get('limit', 20, type=int)
    lang = request.args.get('lang', 'All')
    print(f"[API] /api/trending called with lang={lang}")
    songs = fetch_trending(limit, lang)
    print(f"[API] Returning {len(songs)} songs")
    return jsonify(songs)

@app.route('/api/song/<song_id>')
def api_song(song_id):
    song = fetch_song(song_id)
    if song:
        return jsonify(song)
    return jsonify({"error": "Song not found"}), 404


# ── NEW: ARTISTS API ──────────────────────────────────────────

@app.route('/api/artists')
def api_artists():
    """Get personalized artists based on user taste + language filter."""
    user_id = get_user_id()
    lang = request.args.get('lang', 'All')
    limit = request.args.get('limit', 10, type=int)

    # Get user's taste-based artists first
    taste = get_full_taste_summary(user_id)

    artists = []
    seen = set()

    # 1. From user's top artists (taste-based)
    for artist_name, weight in taste.get('top_artists', [])[:limit]:
        key = artist_name.lower()
        if key in seen:
            continue
        seen.add(key)

        # Detect language
        detected_lang = None
        for a_name, a_lang in ARTIST_LANG_MAP.items():
            if a_name in key or key in a_name:
                detected_lang = a_lang
                break

        # Filter by language
        if lang and lang.lower() != 'all':
            if detected_lang and detected_lang != lang.lower():
                continue

        artists.append({
            'id': key.replace(' ', '_'),
            'name': artist_name,
            'image': '/static/images/default-album.png',
            'language': detected_lang or 'hindi',
            'genre': 'Your Top',
            'source': 'taste'
        })

    # 2. From favorites history
    try:
        favs = db.get_user_favorites(user_id)
        for item in favs:
            raw = item.get('artist', '')
            names = [a.strip() for a in re.split(r'[,/&]', raw) if a.strip()]
            for name in names:
                key = name.lower()
                if key in seen:
                    continue
                seen.add(key)

                detected_lang = None
                for a_name, a_lang in ARTIST_LANG_MAP.items():
                    if a_name in key or key in a_name:
                        detected_lang = a_lang
                        break

                if lang and lang.lower() != 'all':
                    if detected_lang and detected_lang != lang.lower():
                        continue

                artists.append({
                    'id': key.replace(' ', '_'),
                    'name': name,
                    'image': item.get('image_url', '/static/images/default-album.png'),
                    'language': detected_lang or 'hindi',
                    'genre': 'From Favorites',
                    'source': 'favorites'
                })
    except Exception as e:
        print(f"[API_ARTISTS] Favorites error: {e}")

    # 3. From listening history
    try:
        history = db.get_recently_played(user_id, 30)
        for item in history:
            raw = item.get('artist', '')
            names = [a.strip() for a in re.split(r'[,/&]', raw) if a.strip()]
            for name in names:
                key = name.lower()
                if key in seen:
                    continue
                seen.add(key)

                detected_lang = None
                for a_name, a_lang in ARTIST_LANG_MAP.items():
                    if a_name in key or key in a_name:
                        detected_lang = a_lang
                        break

                if lang and lang.lower() != 'all':
                    if detected_lang and detected_lang != lang.lower():
                        continue

                artists.append({
                    'id': key.replace(' ', '_'),
                    'name': name,
                    'image': item.get('image_url', '/static/images/default-album.png'),
                    'language': detected_lang or 'hindi',
                    'genre': 'Recently Played',
                    'source': 'history'
                })
    except Exception as e:
        print(f"[API_ARTISTS] History error: {e}")

    # 4. Fallback to trending artists if we don't have enough
    if len(artists) < limit:
        trending_songs = fetch_trending(limit * 3, lang)
        trending_artists = _extract_artists_from_songs(trending_songs, lang)
        for a in trending_artists:
            if a['id'] not in seen:
                seen.add(a['id'])
                artists.append(a)
            if len(artists) >= limit:
                break

    return jsonify(artists[:limit])


# ── NEW: RECOMMENDATIONS API ──────────────────────────────────

@app.route('/api/recommendations')
def api_recommendations():
    """Get personalized song recommendations filtered by language."""
    user_id = get_user_id()
    limit = request.args.get('limit', 20, type=int)
    lang = request.args.get('lang', 'All')

    # Get trending pool
    trending = fetch_trending(60, lang)

    # Get personalized suggestions
    suggested = get_suggestions_for_user(user_id, trending, limit)

    return jsonify(suggested)


# ── NEW: SIMILAR SONGS API ───────────────────────────────────

@app.route('/api/similar-songs/<song_id>')
def api_similar_songs(song_id):
    """Get songs similar to the given song (same artist/language/genre)."""
    from suggest import get_similar_songs
    limit = request.args.get('limit', 10, type=int)
    lang = request.args.get('lang', 'All')

    # Get current song details
    current = fetch_song(song_id)
    if not current:
        return jsonify([])

    # Search for similar songs
    similar = get_similar_songs(current, limit=limit * 2)

    # Filter by language
    if lang and lang.lower() != 'all':
        similar = _filter_by_language(similar, lang)

    # Exclude the current song itself
    current_id = str(current.get('id', ''))
    similar = [s for s in similar if str(s.get('id', '')) != current_id]

    return jsonify(similar[:limit])


# ── TASTE / SUGGESTION API ─────────────────────────────────────

@app.route('/api/suggestions')
def api_suggestions():
    """GET /api/suggestions?limit=20 — personalised song feed."""
    user_id    = get_user_id()
    limit      = request.args.get('limit', 20, type=int)
    lang       = request.args.get('lang', 'All')
    trending   = fetch_trending(40, lang)
    suggested  = get_suggestions_for_user(user_id, trending, limit)
    return jsonify(suggested)


@app.route('/api/taste')
def api_taste():
    """GET /api/taste — return the user's taste profile summary."""
    user_id = get_user_id()
    taste   = get_full_taste_summary(user_id)
    return jsonify(taste)


@app.route('/api/like', methods=['POST'])
def api_like_song():
    """
    POST { song_id, title, artist, genre, language, mood, tempo, ... }
    Like a song — updates taste tracker AND favorites.
    """
    user_id   = get_user_id()
    data      = request.get_json(silent=True) or {}
    song_data = {
        "song_id":   data.get("song_id"),
        "title":     data.get("title", "Unknown"),
        "artist":    data.get("artist", "Unknown"),
        "album":     data.get("album", ""),
        "genre":     data.get("genre", ""),
        "language":  data.get("language", ""),
        "mood":      data.get("mood", ""),
        "tempo":     data.get("tempo", ""),
        "duration":  data.get("duration", 0),
        "image_url": data.get("image_url") or data.get("image", ""),
        "audio_url": data.get("audio_url") or data.get("url", ""),
        "source":    data.get("source", "jiosaavn"),
    }
    # Toggle favorite (database.py internally calls on_song_liked)
    result = db.toggle_favorite(user_id, song_data)
    return jsonify(result)


# Keep legacy route name working
@app.route('/api/favorite', methods=['POST'])
def api_toggle_favorite():
    return api_like_song()


@app.route('/api/favorites')
def api_get_favorites():
    user_id   = get_user_id()
    favorites = db.get_user_favorites(user_id)
    return jsonify(favorites)

@app.route('/api/history')
def api_get_history():
    user_id = get_user_id()
    limit   = request.args.get('limit', 20, type=int)
    history = db.get_recently_played(user_id, limit)
    return jsonify(history)

@app.route('/api/search-history')
def api_search_history():
    user_id = get_user_id()
    limit   = request.args.get('limit', 10, type=int)
    history = db.get_search_history(user_id, limit)
    return jsonify([h["query"] for h in history])

@app.route('/api/playlist/create', methods=['POST'])
def api_create_playlist():
    user_id     = get_user_id()
    data        = request.get_json() or {}
    name        = data.get("name", "My Playlist")
    description = data.get("description", "")
    result      = db.create_playlist(user_id, name, description)
    return jsonify(result)

@app.route('/api/playlist/<playlist_id>/add', methods=['POST'])
def api_add_to_playlist(playlist_id):
    user_id = get_user_id()
    data    = request.get_json() or {}
    result  = db.add_song_to_playlist(user_id, playlist_id, data)
    return jsonify(result)

@app.route('/api/playlist/<playlist_id>/delete', methods=['POST'])
def api_delete_playlist(playlist_id):
    user_id        = get_user_id()
    data           = db._load("playlists")
    user_playlists = data.get(user_id, [])
    original_len   = len(user_playlists)
    user_playlists = [pl for pl in user_playlists if pl["playlist_id"] != playlist_id]
    if len(user_playlists) < original_len:
        data[user_id] = user_playlists
        db._save("playlists", data)
        return jsonify({"success": True, "message": "Playlist deleted"})
    return jsonify({"success": False, "message": "Playlist not found"}), 404

@app.route('/api/playlists')
def api_get_playlists():
    user_id       = get_user_id()
    playlists_data = db.get_user_playlists(user_id)
    return jsonify(playlists_data)

@app.route('/api/stats')
def api_stats():
    user_id       = get_user_id()
    favorites     = db.get_user_favorites(user_id)
    playlists_data = db.get_user_playlists(user_id)
    recent        = db.get_recently_played(user_id, 9999)
    return jsonify({
        "total_favorites": len(favorites),
        "total_playlists": len(playlists_data),
        "total_plays":     len(recent),
        "listening_hours": round(len(recent) * 3.5 / 60, 1)
    })

@app.route('/api/profile/update', methods=['POST'])
def api_update_profile():
    user_id = get_user_id()
    data    = request.get_json(silent=True) or {}

    users = db._load("users")
    if user_id not in users:
        return jsonify({"success": False, "message": "User not found"}), 404

    user    = users[user_id]
    allowed = ["display_name", "bio", "avatar_url", "email"]
    for key in allowed:
        if key in data:
            user[key] = data[key]

    if any(k in data for k in ["instagram", "twitter", "youtube", "spotify"]):
        social = user.get("social_links", {})
        for key in ["instagram", "twitter", "youtube", "spotify"]:
            if key in data:
                social[key] = data[key]
        user["social_links"] = social

    if any(k in data for k in ["theme", "accent_color", "notifications", "auto_play", "text_size", "download_quality"]):
        prefs = user.get("preferences", {})
        for key in ["theme", "accent_color", "notifications", "auto_play", "text_size", "download_quality"]:
            if key in data:
                prefs[key] = data[key]
        user["preferences"] = prefs

    from datetime import datetime, timezone
    user["updated_at"] = datetime.now(timezone.utc).isoformat()
    db._save("users", users)
    return jsonify({"success": True, "message": "Profile updated"})


@app.route('/api/profile/delete', methods=['POST'])
def api_delete_profile():
    user_id = get_user_id()
    for store in ["users", "favorites", "recently_played", "playlists", "search_history", "taste_profiles"]:
        data = db._load(store)
        if user_id in data:
            del data[user_id]
            db._save(store, data)
    from refresh import clear_session_skips
    clear_session_skips()
    session.clear()
    return jsonify({"success": True, "message": "Account deleted"})


@app.route('/api/debug')
def api_debug():
    try:
        r          = requests.get(f"{API_BASE_URL}/", timeout=10)
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
    print(f"[500 ERROR] {e}")
    print(traceback.format_exc())
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
