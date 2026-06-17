"""
user/trackuser.py  —  EvaMusic taste tracking & user profile engine

What changed:
- on_song_liked() now actually updates taste profile (was 'pass')
- on_song_played() now updates taste profile on every play
- on_song_skipped() — NEW: tracks skipped songs
- get_disliked_songs() — NEW: returns list of disliked song IDs
- get_preferred_mood() now reads from real taste data (was hardcoded "happy")
- _update_taste_profile() tracks artists, genres, languages, moods, tempos
- Taste profiles stored in JSON file (no database dependency)
"""

import os
import json
from collections import Counter

# Taste profile storage path
TASTE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
TASTE_FILE = os.path.join(TASTE_DIR, 'taste_profiles.json')

# Ensure data directory exists
os.makedirs(TASTE_DIR, exist_ok=True)


def _load_taste_profiles():
    """Load all taste profiles from JSON file."""
    if not os.path.exists(TASTE_FILE):
        return {}
    try:
        with open(TASTE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_taste_profiles(profiles):
    """Save all taste profiles to JSON file."""
    try:
        with open(TASTE_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"[TASTE] Save error: {e}")
        return False


def get_taste_profile(user_id):
    """Get a single user's taste profile."""
    profiles = _load_taste_profiles()
    return profiles.get(user_id, {})


def save_taste_profile(user_id, taste_data):
    """Save a single user's taste profile."""
    profiles = _load_taste_profiles()
    profiles[user_id] = taste_data
    return _save_taste_profiles(profiles)


def _update_taste_profile(user_id, song_data):
    """
    Update the user's taste profile when they interact with a song
    (play, like, or search).
    """
    # Load existing taste profile
    taste = get_taste_profile(user_id) or {}

    # Initialize counters if not present
    if 'artists' not in taste:
        taste['artists'] = {}
    if 'genres' not in taste:
        taste['genres'] = {}
    if 'languages' not in taste:
        taste['languages'] = {}
    if 'moods' not in taste:
        taste['moods'] = {}
    if 'tempos' not in taste:
        taste['tempos'] = {}
    if 'play_count' not in taste:
        taste['play_count'] = 0
    if 'skipped' not in taste:
        taste['skipped'] = []
    if 'disliked' not in taste:
        taste['disliked'] = []

    # Increment total play count
    taste['play_count'] = taste.get('play_count', 0) + 1

    # Update artists
    artist = song_data.get('artist', 'Unknown')
    if artist and artist != 'Unknown':
        artists = taste['artists']
        artists[artist] = artists.get(artist, 0) + 1
        taste['artists'] = artists

    # Update genres
    genre = song_data.get('genre', '')
    if genre and genre != 'Unknown' and genre != '':
        genres = taste['genres']
        genres[genre] = genres.get(genre, 0) + 1
        taste['genres'] = genres

    # Update languages
    language = song_data.get('language', '')
    if language and language != 'Unknown' and language != '':
        langs = taste['languages']
        langs[language] = langs.get(language, 0) + 1
        taste['languages'] = langs

    # Update moods
    mood = song_data.get('mood', '')
    if mood and mood != 'Unknown' and mood != '':
        moods = taste['moods']
        moods[mood] = moods.get(mood, 0) + 1
        taste['moods'] = moods

    # Update tempos
    tempo = song_data.get('tempo', '')
    if tempo and tempo != 'Unknown' and tempo != '':
        tempos = taste['tempos']
        tempos[tempo] = tempos.get(tempo, 0) + 1
        taste['tempos'] = tempos

    # Save updated taste profile
    save_taste_profile(user_id, taste)

    return taste


def on_song_liked(user_id, song_data):
    """
    Called when a user likes/favorites a song.
    Updates taste profile with the song's metadata.
    """
    # Update taste profile with this song's data
    _update_taste_profile(user_id, song_data)

    # Also increment a 'like' counter
    taste = get_taste_profile(user_id) or {}
    if 'likes' not in taste:
        taste['likes'] = 0
    taste['likes'] = taste.get('likes', 0) + 1
    save_taste_profile(user_id, taste)

    return {"success": True, "message": "Taste profile updated"}


def on_song_played(user_id, song_data, listen_seconds=60):
    """
    Called when a user plays a song.
    Updates taste profile with the song's metadata.
    listen_seconds: how long user listened (default 60 sec)
    """
    # Only count as a full play if listened for at least 30 seconds
    if listen_seconds >= 30:
        return _update_taste_profile(user_id, song_data)
    return get_taste_profile(user_id) or {}


def on_song_skipped(user_id, song_data, listen_seconds=3):
    """
    Called when a user skips a song.
    Tracks skipped songs so they don't get recommended again.
    listen_seconds: how long user listened before skipping (default 3 sec)
    """
    taste = get_taste_profile(user_id) or {}

    if 'skipped' not in taste:
        taste['skipped'] = []

    song_id = song_data.get('song_id') or song_data.get('id')
    if song_id and song_id not in taste['skipped']:
        taste['skipped'].append(song_id)
        # Keep only last 100 skipped songs
        if len(taste['skipped']) > 100:
            taste['skipped'] = taste['skipped'][-100:]

    # Track skip count per artist
    artist = song_data.get('artist', 'Unknown')
    if artist and artist != 'Unknown':
        if 'skip_artists' not in taste:
            taste['skip_artists'] = {}
        taste['skip_artists'][artist] = taste['skip_artists'].get(artist, 0) + 1

    save_taste_profile(user_id, taste)
    return {"success": True, "message": "Skip recorded"}


def get_disliked_songs(user_id):
    """
    Get list of song IDs that the user has skipped/disliked.
    Used by recommendation engine to filter out unwanted songs.
    """
    taste = get_taste_profile(user_id) or {}
    return taste.get('skipped', [])


def get_full_taste_summary(user_id):
    """
    Return a formatted summary of the user's taste profile.
    Includes top artists, genres, languages, moods, tempos.
    """
    taste = get_taste_profile(user_id) or {}

    # Get top items sorted by count
    def get_top_items(data_dict, limit=5):
        if not data_dict:
            return []
        sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:limit]

    summary = {
        'top_artists': get_top_items(taste.get('artists', {}), 10),
        'top_genres': get_top_items(taste.get('genres', {}), 5),
        'top_languages': get_top_items(taste.get('languages', {}), 5),
        'top_moods': get_top_items(taste.get('moods', {}), 5),
        'top_tempos': get_top_items(taste.get('tempos', {}), 5),
        'total_plays': taste.get('play_count', 0),
        'total_likes': taste.get('likes', 0),
        'total_skipped': len(taste.get('skipped', [])),
    }

    return summary


def get_preferred_mood(user_id):
    """
    Get the user's most preferred mood based on their taste profile.
    Returns the top mood or 'happy' as fallback.
    """
    taste = get_taste_profile(user_id) or {}
    moods = taste.get('moods', {})

    if not moods:
        return 'happy'  # Default fallback for new users

    # Return the most played mood
    top_mood = max(moods.items(), key=lambda x: x[1])[0]
    return top_mood


def get_preferred_language(user_id):
    """
    Get the user's most preferred language based on their taste profile.
    """
    taste = get_taste_profile(user_id) or {}
    languages = taste.get('languages', {})

    if not languages:
        return 'hindi'  # Default fallback

    top_lang = max(languages.items(), key=lambda x: x[1])[0]
    return top_lang


def get_preferred_artists(user_id, limit=5):
    """
    Get the user's most preferred artists.
    """
    taste = get_taste_profile(user_id) or {}
    artists = taste.get('artists', {})

    if not artists:
        return []

    sorted_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)
    return [a[0] for a in sorted_artists[:limit]]


def reset_taste_profile(user_id):
    """
    Reset the user's taste profile to empty.
    """
    empty_profile = {
        'artists': {},
        'genres': {},
        'languages': {},
        'moods': {},
        'tempos': {},
        'play_count': 0,
        'likes': 0,
        'skipped': [],
        'disliked': [],
        'skip_artists': {},
    }
    save_taste_profile(user_id, empty_profile)
    return {"success": True, "message": "Taste profile reset"}
