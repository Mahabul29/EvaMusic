import os
import random
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# ═══════════════════════════════════════════════════════════════════════
# API configs — (base, search_path, param_key)
#
# These are unofficial community-hosted JioSaavn API mirrors. They tend to
# go down / get rate-limited individually, so we keep a larger pool and
# rotate through them with retries instead of relying on just one or two.
# ═══════════════════════════════════════════════════════════════════════

SEARCH_CONFIGS = [
    ("https://jiosaavn-api-2.vercel.app",        "/api/search/songs", "query"),
    ("https://saavn.dev",                        "/api/search/songs", "query"),
    ("https://jiosaavn-api-ts.vercel.app",       "/api/search/songs", "query"),
    ("https://jiosaavn-api-sigma.vercel.app",    "/api/search/songs", "query"),
    ("https://jiosaavn-api-tau.vercel.app",      "/api/search/songs", "query"),
    ("https://jiosaavn-api-codewithwilliam.vercel.app", "/api/search/songs", "query"),
    ("https://jio-saavn-api.vercel.app",         "/search/songs",     "query"),
    ("https://jio-saavn-api.vercel.app",         "/search",           "query"),
    ("https://saavn-api-eight.vercel.app",       "/api/search/songs", "query"),
]

# For song / album / playlist / artist detail lookups (non-search)
API_BASES = [
    "https://jiosaavn-api-2.vercel.app/api",
    "https://saavn.dev/api",
    "https://jiosaavn-api-ts.vercel.app/api",
    "https://jiosaavn-api-sigma.vercel.app/api",
    "https://jiosaavn-api-tau.vercel.app/api",
    "https://jiosaavn-api-codewithwilliam.vercel.app/api",
    "https://jio-saavn-api.vercel.app",
    "https://saavn-api-eight.vercel.app/api",
]

# A small set of always-available, royalty-free tracks used ONLY as a last
# resort so the UI never shows a completely empty trending/home page even
# if every JioSaavn mirror above is down or rate-limited.
FALLBACK_SONGS = [
    {
        "id": "fallback-1",
        "title": "SoundHelix Song 1",
        "artist": "SoundHelix",
        "album": "Demo Tracks",
        "image": "/static/images/default-album.png",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "duration": 300,
        "year": "",
    },
    {
        "id": "fallback-2",
        "title": "SoundHelix Song 2",
        "artist": "SoundHelix",
        "album": "Demo Tracks",
        "image": "/static/images/default-album.png",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "duration": 300,
        "year": "",
    },
    {
        "id": "fallback-3",
        "title": "SoundHelix Song 3",
        "artist": "SoundHelix",
        "album": "Demo Tracks",
        "image": "/static/images/default-album.png",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "duration": 300,
        "year": "",
    },
    {
        "id": "fallback-4",
        "title": "SoundHelix Song 4",
        "artist": "SoundHelix",
        "album": "Demo Tracks",
        "image": "/static/images/default-album.png",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "duration": 300,
        "year": "",
    },
    {
        "id": "fallback-5",
        "title": "SoundHelix Song 5",
        "artist": "SoundHelix",
        "album": "Demo Tracks",
        "image": "/static/images/default-album.png",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
        "duration": 300,
        "year": "",
    },
    {
        "id": "fallback-6",
        "title": "SoundHelix Song 6",
        "artist": "SoundHelix",
        "album": "Demo Tracks",
        "image": "/static/images/default-album.png",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "duration": 300,
        "year": "",
    },
]

# In-memory cache of the last successful trending fetch. If a later request
# fails (mirror down / rate-limited), we serve this instead of an empty list.
_LAST_GOOD_TRENDING = []

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# How many times to retry the FULL list of mirrors before giving up.
MAX_ROUNDS = 2


def _get(url, params=None, timeout=20):
    """GET a full URL; return parsed JSON only if non-empty."""
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        print(f"[API] {r.status_code} from {url} params={params}")
        if r.status_code == 200:
            try:
                data = r.json()
            except ValueError:
                print(f"[API] Non-JSON response from {url}")
                return None
            if data and data != {} and data != []:
                return data
            print(f"[API] Empty body from {url}")
        elif r.status_code == 429:
            print(f"[API] Rate limited by {url}")
    except requests.exceptions.Timeout:
        print(f"[API ERROR] Timeout: {url}")
    except Exception as e:
        print(f"[API ERROR] {url}: {e}")
    return None


def _get_path(path, params=None, timeout=20):
    """Try path against each base in API_BASES, with multiple rounds."""
    for round_num in range(MAX_ROUNDS):
        for base in API_BASES:
            data = _get(f"{base}{path}", params, timeout)
            if data:
                return data
    return None

# ═══════════════════════════════════════════════════════════════════════


def fetch_songs(query, limit=20):
    """Search for songs across all configured mirrors, with retry rounds."""
    for round_num in range(MAX_ROUNDS):
        for base, path, key in SEARCH_CONFIGS:
            data = _get(f"{base}{path}", {key: query, "limit": limit})
            if data:
                songs = _extract_songs(data)
                if songs:
                    print(f"[SEARCH] '{query}' -> {len(songs)} songs via {base}{path} (round {round_num + 1})")
                    return songs
        if round_num < MAX_ROUNDS - 1:
            print(f"[SEARCH] Round {round_num + 1} failed for '{query}', retrying...")
    print(f"[SEARCH] No results for '{query}' after {MAX_ROUNDS} rounds")
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
    global _LAST_GOOD_TRENDING

    queries = [
        "trending bollywood 2024",
        "top hindi songs",
        "arijit singh hits",
        "bollywood new releases",
        "viral songs india",
        "top english songs 2024",
        "punjabi hits",
        "latest songs",
    ]

    # Try a handful of different queries (not just one random pick) so a
    # single mirror being down for that exact query doesn't sink the whole
    # trending page.
    tried = random.sample(queries, k=min(3, len(queries)))
    for q in tried:
        songs = fetch_songs(q, limit)
        if songs:
            _LAST_GOOD_TRENDING = songs
            return songs

    # Nothing worked this time — fall back to the last successful result
    # if we have one, so the page doesn't suddenly go empty.
    if _LAST_GOOD_TRENDING:
        print("[TRENDING] All queries failed, serving cached trending results")
        return _LAST_GOOD_TRENDING

    print("[TRENDING] All queries failed and no cache available")
    return []


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


def _with_fallback(songs, limit=None):
    """Top up a (possibly empty/short) list of playable songs with the
    hardcoded fallback tracks so the UI never looks completely dead."""
    songs = list(songs)
    if len(songs) == 0:
        songs = list(FALLBACK_SONGS)
    if limit:
        songs = songs[:limit]
    return songs

# ═══════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    trending = fetch_trending(12)
    songs = [format_song(x) for x in trending]
    songs_with_url = [s for s in songs if s.get("url")]
    songs_with_url = _with_fallback(songs_with_url, 12)
    print(f"[HOME] {len(songs_with_url)} songs have stream URLs")
    return render_template('index.html', songs=songs_with_url, title="Home")


@app.route('/search')
def search():
    query = request.args.get('q', '')
    songs = []
    if query:
        results = fetch_songs(query, 30)
        songs = [format_song(x) for x in results]
        songs_with_url = [s for s in songs if s.get("url")]
        print(f"[SEARCH] '{query}' -> {len(songs)} total, {len(songs_with_url)} streamable")
        songs = songs_with_url
    return render_template('search.html', songs=songs, query=query, title="Search")


@app.route('/player/<song_id>')
def player(song_id):
    # Serve hardcoded fallback songs directly if requested.
    for fb in FALLBACK_SONGS:
        if fb["id"] == song_id:
            return render_template('player.html', song=fb, title=fb["title"])

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
    songs = _with_fallback(songs, 24)
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
    songs = _with_fallback(songs, limit)
    return jsonify(songs)


@app.route('/api/song/<song_id>')
def api_song(song_id):
    for fb in FALLBACK_SONGS:
        if fb["id"] == song_id:
            return jsonify(fb)

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
        results.append({
            "url": url,
            "got_data": bool(data),
            "songs": len(_extract_songs(data)) if data else 0,
        })
    return jsonify(results)


@app.route('/api/debug/detail')
def api_debug_detail():
    """Check which API_BASES respond for a detail-style endpoint."""
    song_id = request.args.get('id', '')
    results = []
    for base in API_BASES:
        url = f"{base}/songs/{song_id}" if song_id else f"{base}/songs"
        data = _get(url, None)
        results.append({"url": url, "got_data": bool(data)})
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
