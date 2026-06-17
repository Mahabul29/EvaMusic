"""
user/trackuser.py  —  EvaMusic taste tracking & user profile engine
Fully restored with comprehensive structure vectors to stop dashboard white screens.
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

def get_taste_profile(user_id):
    profiles = _load_taste_profiles()
    return profiles.get(user_id, {})

# ═══════════════════════════════════════════════════════════════
# SIGNATURE HOOKS FOR REFRESH.PY & DATABASE
# ═══════════════════════════════════════════════════════════════

def on_song_liked(user_id, song_data):
    profiles = _load_taste_profiles()
    user_p = profiles.setdefault(user_id, {
        "artists": {}, "languages": {}, "genres": {}, "moods": {}, "skips": []
    })
    
    artist = (song_data.get('artist') or 'Unknown').split(',')[0].strip()
    user_p.setdefault("artists", {})[artist] = user_p["artists"].get(artist, 0) + 5
    
    lang = song_data.get('language', 'hindi').lower()
    user_p.setdefault("languages", {})[lang] = user_p["languages"].get(lang, 0) + 5
    
    _save_taste_profiles(profiles)

def on_song_played(user_id, song_data, listen_seconds=60):
    profiles = _load_taste_profiles()
    user_p = profiles.setdefault(user_id, {
        "artists": {}, "languages": {}, "genres": {}, "moods": {}, "skips": []
    })
    
    artist = (song_data.get('artist') or 'Unknown').split(',')[0].strip()
    user_p.setdefault("artists", {})[artist] = user_p["artists"].get(artist, 0) + 1
    
    _save_taste_profiles(profiles)

def on_song_skipped(user_id, song_data, listen_seconds=3):
    profiles = _load_taste_profiles()
    user_p = profiles.setdefault(user_id, {
        "artists": {}, "languages": {}, "genres": {}, "moods": {}, "skips": []
    })
    
    skips_list = user_p.setdefault("skips", [])
    sid = str(song_data.get('id') or song_data.get('song_id', ''))
    if sid and sid not in skips_list:
        skips_list.append(sid)
    _save_taste_profiles(profiles)

def get_disliked_songs(user_id):
    profiles = _load_taste_profiles()
    return profiles.get(user_id, {}).get("skips", [])

# ═══════════════════════════════════════════════════════════════
# ORIGINAL COMPATIBILITY FALLBACKS
# ═══════════════════════════════════════════════════════════════

def get_preferred_mood(user_id):
    taste = get_taste_profile(user_id)
    moods = taste.get('moods', {})
    return max(moods.items(), key=lambda x: x[1])[0] if moods else 'happy'

def get_preferred_language(user_id):
    taste = get_taste_profile(user_id)
    languages = taste.get('languages', {})
    return max(languages.items(), key=lambda x: x[1])[0] if languages else 'hindi'

def get_preferred_artists(user_id, limit=5):
    taste = get_taste_profile(user_id)
    artists = taste.get('artists', {})
    sorted_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)
    return [a[0] for a in sorted_artists[:limit]]

def reset_taste_profile(user_id):
    profiles = _load_taste_profiles()
    profiles[user_id] = {"artists": {}, "languages": {}, "genres": {}, "moods": {}, "skips": []}
    _save_taste_profiles(profiles)

# ═══════════════════════════════════════════════════════════════
# MAIN HOMEPAGE ANALYTICS STRUCTURE EXPORTER
# ═══════════════════════════════════════════════════════════════

def get_full_taste_summary(user_id):
    profiles = _load_taste_profiles()
    user_p = profiles.get(user_id, {})
    
    artists = sorted(user_p.get("artists", {}).items(), key=lambda x: x[1], reverse=True)
    languages = sorted(user_p.get("languages", {}).items(), key=lambda x: x[1], reverse=True)
    genres = sorted(user_p.get("genres", {}).items(), key=lambda x: x[1], reverse=True)
    moods = sorted(user_p.get("moods", {}).items(), key=lambda x: x[1], reverse=True)
    
    return {
        'top_artists': artists[:10],
        'top_languages': [(l.title(), w) for l, w in languages[:5]] if languages else [('Hindi', 1)],
        'top_genres': genres[:5],
        'top_moods': moods[:3] if moods else [('Chill', 1)],
        'metrics_collected': len(artists) + len(languages)
    }
    
