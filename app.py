import os
import requests
import uuid
import re
import html
from flask import Flask, render_template, jsonify, request, send_from_directory, session
from config import get_search_url, get_trending_url, get_song_url, API_BASE_URL

import database as db

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-to-something-random-abc123_2026')

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

def _call(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API EXCEPTION] URL {url}: {e}")
    return None

def _clean_string(s):
    if not s: return ""
    s = html.unescape(s) if hasattr(html, 'unescape') else s
    s = re.sub(r'&\w+;', '', s)
    return s.strip()

def _normalize_song(s):
    if not s: return None
    
    media_urls = s.get("download_url") or s.get("downloadUrl") or []
    audio_url = ""
    if isinstance(media_urls, list) and media_urls:
        best = [m for m in media_urls if isinstance(m, dict) and "320" in str(m.get("quality", ""))]
        if not best:
            best = [m for m in media_urls if isinstance(m, dict) and "160" in str(m.get("quality", ""))]
        if not best:
            best = media_urls
        if best and isinstance(best[0], dict):
            audio_url = best[0].get("url") or best[0].get("link") or ""
            
    images = s.get("image") or []
    image_url = "/static/images/default-album.png"
    if isinstance(images, list) and images:
        best_img = [i for i in images if isinstance(i, dict) and "500" in str(i.get("quality", ""))]
        if not best_img:
            best_img = images
        if best_img and isinstance(best_img[0], dict):
            image_url = best_img[0].get("url") or best_img[0].get("link") or image_url

    artists_data = s.get("artists") or {}
    primary_list = artists_data.get("primary") or []
    artist_names = [a.get("name") for a in primary_list if isinstance(a, dict) and a.get("name")]
    if not artist_names:
        artist_names = [s.get("artist")] if s.get("artist") else ["Unknown Artist"]
    artist_str = ", ".join(filter(None, artist_names))

    title = s.get("name") or s.get("title") or "Unknown Song"
    album_data = s.get("album") or {}
    album_name = album_data.get("name") if isinstance(album_data, dict) else s.get("album") or ""

    return {
        "id":        str(s.get("id", "")),
        "title":     _clean_string(title),
        "artist":    _clean_string(artist_str),
        "album":     _clean_string(album_name),
        "image":     image_url,
        "url":       audio_url,
        "duration":  int(s.get("duration") or 0)
    }

# Helper to fetch general music arrays safely for background requests
def _get_cached_trending_pool():
    trending_api_url = get_trending_url(limit=40)
    raw_trending = _call(trending_api_url)
    if raw_trending and isinstance(raw_trending, dict):
        data_node = raw_trending.get("data") or raw_trending.get("results") or []
        if isinstance(data_node, dict):
            data_node = data_node.get("songs") or data_node.get("trending") or []
        if isinstance(data_node, list):
            songs = [_normalize_song(x) for x in data_node if x]
            return [x for x in songs if x and x.get("url")]
    return []

@app.route('/')
@app.route('/home')
def home():
    user_id = get_user_id()
    selected_languages = session.get('selected_languages', ['hindi', 'english'])

    trending_songs = _get_cached_trending_pool()

    homepage_data = {
        "trending": trending_songs[:12],
        "charts": trending_songs[12:24] if len(trending_songs) > 12 else [],
        "new_releases": trending_songs[24:36] if len(trending_songs) > 24 else [],
        "personalized": False
    }

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

# ═══════════════════════════════════════════════════════════════
# FRONTEND RECOVERY ENDPOINTS (PREVENTS JAVASCRIPT WHITE SCREENS)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/artists')
def api_fallback_artists():
    return jsonify([])  # Prevents crash if 'loadArtists()' expects data array

@app.route('/api/suggestions')
def api_fallback_suggestions():
    # Returns basic trending tracks so section-because-liked fills with content instead of failing
    return jsonify(_get_cached_trending_pool()[:8])

@app.route('/api/usuals')
def api_fallback_usuals():
    return jsonify([])  # Instructs new layout to slide straight to trending fallback cards

# ═══════════════════════════════════════════════════════════════
# STANDARD APP ROUTINGS
# ═══════════════════════════════════════════════════════════════

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    user_id = get_user_id()
    songs = []
    
    if query:
        db.add_to_search_history(user_id, query)
        raw = _call(get_search_url(query))
        if raw and isinstance(raw, dict):
            data_node = raw.get("data") or raw.get("results") or []
            if isinstance(data_node, dict):
                data_node = data_node.get("songs") or []
            if isinstance(data_node, list):
                songs = [_normalize_song(x) for x in data_node if x]
                songs = [x for x in songs if x and x.get("url")]

    return render_template('index.html', songs=songs, query=query, title=f"Results for '{query}'")

@app.route('/api/languages', methods=['POST'])
def save_languages():
    data = request.get_json(silent=True) or {}
    langs = data.get('languages', ['hindi'])
    if not isinstance(langs, list) or not langs:
        langs = ['hindi']
    session['selected_languages'] = [str(l).lower() for l in langs]
    return jsonify({"success": True})

@app.route('/api/favorites/toggle', methods=['POST'])
def api_toggle_favorite():
    user_id = get_user_id()
    song_data = request.get_json(silent=True) or {}
    if not song_data.get('id'):
        return jsonify({"success": False, "message": "Missing song ID"}), 400
    res = db.toggle_favorite(user_id, song_data)
    return jsonify(res)

@app.route('/api/history/add', methods=['POST'])
def api_add_history():
    user_id = get_user_id()
    song_data = request.get_json(silent=True) or {}
    if not song_data.get('id'):
        return jsonify({"success": False}), 400
    db.add_to_history(user_id, song_data)
    return jsonify({"success": True})

@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    db.clear_history(get_user_id())
    return jsonify({"success": True})

@app.route('/api/account/delete', methods=['POST'])
def api_delete_account():
    user_id = get_user_id()
    db.clear_history(user_id)
    session.clear()
    return jsonify({"success": True, "message": "Account deleted"})

@app.route('/api/debug')
def api_debug():
    try:
        r = requests.get(f"{API_BASE_URL}/", timeout=10)
        api_status = r.status_code
    except Exception as e:
        api_status = f"error: {e}"
    db_health = db.check_db_health()
    return jsonify({"api_base": API_BASE_URL, "api_status": api_status, "db_health": db_health})

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html', songs=[], title="Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server crash suppressed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
    
