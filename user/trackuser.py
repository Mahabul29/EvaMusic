"""
user/trackuser.py  —  User Profile and Taste Modeling Engine
Adjusted positional argument tracking limits to prevent runtime errors.
"""

import os
import json
from collections import Counter

TASTE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
TASTE_FILE = os.path.join(TASTE_DIR, 'taste_profiles.json')
os.makedirs(TASTE_DIR, exist_ok=True)

def _load_taste_profiles():
    if not os.path.exists(TASTE_FILE):
        return {}
    try:
        with open(TASTE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_taste_profiles(profiles):
    try:
        with open(TASTE_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════
# SIGNATURE HOOKS FOR REFRESH.PY
# ═══════════════════════════════════════════════════════════════

def on_song_liked(user_id, song_data):
    profiles = _load_taste_profiles()
    if user_id not in profiles:
        profiles[user_id] = {"artists": {}, "languages": {}, "genres": {}, "skips": []}
    
    artist = (song_data.get('artist') or 'Unknown').split(',')[0].strip()
    artists_map = profiles[user_id].setdefault("artists", {})
    artists_map[artist] = artists_map.get(artist, 0) + 5
    _save_taste_profiles(profiles)

def on_song_played(user_id, song_data, listen_seconds=60):
    profiles = _load_taste_profiles()
    if user_id not in profiles:
        profiles[user_id] = {"artists": {}, "languages": {}, "genres": {}, "skips": []}
        
    artist = (song_data.get('artist') or 'Unknown').split(',')[0].strip()
    artists_map = profiles[user_id].setdefault("artists", {})
    artists_map[artist] = artists_map.get(artist, 0) + 1
    _save_taste_profiles(profiles)

def on_song_skipped(user_id, song_data, listen_seconds=3):
    profiles = _load_taste_profiles()
    if user_id not in profiles:
        profiles[user_id] = {"artists": {}, "languages": {}, "genres": {}, "skips": []}
        
    skips_list = profiles[user_id].setdefault("skips", [])
    sid = str(song_data.get('id') or song_data.get('song_id', ''))
    if sid and sid not in skips_list:
        skips_list.append(sid)
    _save_taste_profiles(profiles)

def get_disliked_songs(user_id):
    profiles = _load_taste_profiles()
    if user_id in profiles:
        return profiles[user_id].get("skips", [])
    return []

# ═══════════════════════════════════════════════════════════════
# ANALYTICS DISPLAY GENERATION
# ═══════════════════════════════════════════════════════════════

def get_full_taste_summary(user_id):
    profiles = _load_taste_profiles()
    user_p = profiles.get(user_id, {})
    
    artists = sorted(user_p.get("artists", {}).items(), key=lambda x: x[1], reverse=True)
    languages = sorted(user_p.get("languages", {}).items(), key=lambda x: x[1], reverse=True)
    genres = sorted(user_p.get("genres", {}).items(), key=lambda x: x[1], reverse=True)
    
    if not artists:
        return {
            'top_artists': [],
            'top_languages': [('Hindi', 1)],
            'top_genres': [],
            'top_moods': [('Chill', 1)],
            'metrics_collected': 0
        }
        
    return {
        'top_artists': artists[:5],
        'top_languages': languages[:3] if languages else [('Hindi', 1)],
        'top_genres': genres[:3],
        'top_moods': [('Chill', 1)],
        'metrics_collected': len(artists)
    }
    
