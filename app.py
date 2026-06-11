import os
import random
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# ─── JioSaavn API Helpers ─────────────────────────────────────────────

JIOSAAVN_API = "https://saavn.dev/api"

def fetch_songs(query, limit=20):
    """Search songs via JioSaavn API"""
    try:
        url = f"{JIOSAAVN_API}/search/songs"
        params = {"query": query, "limit": limit}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("data", {}).get("results", [])
    except Exception as e:
        print(f"Search error: {e}")
        return []

def fetch_trending(limit=20):
    """Get trending songs"""
    try:
        # Using search with popular query as fallback
        queries = ["trending", "top hits", "viral", "new releases"]
        query = random.choice(queries)
        return fetch_songs(query, limit)
    except Exception as e:
        print(f"Trending error: {e}")
        return []

def fetch_playlist_songs(playlist_id):
    """Fetch songs from a playlist"""
    try:
        url = f"{JIOSAAVN_API}/playlists"
        params = {"id": playlist_id}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("data", {}).get("songs", [])
    except Exception as e:
        print(f"Playlist error: {e}")
        return []

def fetch_album_songs(album_id):
    """Fetch songs from an album"""
    try:
        url = f"{JIOSAAVN_API}/albums"
        params = {"id": album_id}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("data", {}).get("songs", [])
    except Exception as e:
        print(f"Album error: {e}")
        return []

def fetch_artist_songs(artist_id, limit=20):
    """Fetch songs by artist"""
    try:
        url = f"{JIOSAAVN_API}/artists/{artist_id}/songs"
        params = {"limit": limit}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("data", {}).get("songs", [])
    except Exception as e:
        print(f"Artist error: {e}")
        return []

def format_song(song):
    """Standardize song data for player"""
    return {
        "id": song.get("id", ""),
        "title": song.get("name", "Unknown Title"),
        "artist": ", ".join([a.get("name", "") for a in song.get("artists", {}).get("primary", [])]) or "Unknown Artist",
        "album": song.get("album", {}).get("name", "Unknown Album"),
        "image": song.get("image", [{}])[-1].get("url", "/static/images/default-album.png"),
        "url": song.get("downloadUrl", [{}])[-1].get("url", ""),
        "duration": song.get("duration", 0),
        "year": song.get("year", ""),
    }

# ─── Routes ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Homepage with trending songs"""
    trending = fetch_trending(12)
    songs = [format_song(s) for s in trending]
    return render_template('index.html', songs=songs, title="Home")

@app.route('/search')
def search():
    """Search page"""
    query = request.args.get('q', '')
    songs = []
    if query:
        results = fetch_songs(query, 30)
        songs = [format_song(s) for s in results]
    return render_template('search.html', songs=songs, query=query, title="Search")

@app.route('/player/<song_id>')
def player(song_id):
    """Music player page"""
    # Fetch song details
    try:
        url = f"{JIOSAAVN_API}/songs/{song_id}"
        response = requests.get(url, timeout=10)
        data = response.json()
        song_data = data.get("data", [{}])[0]
        song = format_song(song_data)
    except:
        song = {"id": song_id, "title": "Unknown", "artist": "Unknown", "url": "", "image": "/static/images/default-album.png"}
    
    return render_template('player.html', song=song, title=song.get("title", "Player"))

@app.route('/trending')
def trending():
    """Trending songs page"""
    songs_raw = fetch_trending(24)
    songs = [format_song(s) for s in songs_raw]
    return render_template('trending.html', songs=songs, title="Trending")

@app.route('/library')
def library():
    """User library page"""
    return render_template('library.html', title="Your Library")

@app.route('/playlist/<playlist_id>')
def playlist(playlist_id):
    """Playlist page"""
    songs_raw = fetch_playlist_songs(playlist_id)
    songs = [format_song(s) for s in songs_raw]
    return render_template('playlist.html', songs=songs, title="Playlist")

@app.route('/album/<album_id>')
def album(album_id):
    """Album page"""
    songs_raw = fetch_album_songs(album_id)
    songs = [format_song(s) for s in songs_raw]
    return render_template('album.html', songs=songs, title="Album")

@app.route('/artist/<artist_id>')
def artist(artist_id):
    """Artist page"""
    songs_raw = fetch_artist_songs(artist_id, 20)
    songs = [format_song(s) for s in songs_raw]
    return render_template('artist.html', songs=songs, title="Artist")

@app.route('/offline')
def offline():
    """Offline page for PWA"""
    return render_template('offline.html', title="Offline")

# ─── API Endpoints ────────────────────────────────────────────────────

@app.route('/api/search')
def api_search():
    """JSON API for search"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    results = fetch_songs(query, limit)
    return jsonify([format_song(s) for s in results])

@app.route('/api/trending')
def api_trending():
    """JSON API for trending"""
    limit = request.args.get('limit', 20, type=int)
    results = fetch_trending(limit)
    return jsonify([format_song(s) for s in results])

@app.route('/api/song/<song_id>')
def api_song(song_id):
    """Get single song details"""
    try:
        url = f"{JIOSAAVN_API}/songs/{song_id}"
        response = requests.get(url, timeout=10)
        data = response.json()
        song_data = data.get("data", [{}])[0]
        return jsonify(format_song(song_data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Static Files & Error Handlers ────────────────────────────────────

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
            
