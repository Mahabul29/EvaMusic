"""
EvaMusic — User Taste Tracker
Tracks exactly what kind of songs each user likes:
genres, artists, languages, moods, tempo, and more.
Updated on every play, like, skip, and playlist-add event.
"""

import json
import os
from datetime import datetime, timezone

# Data lives inside /workspace/data/ — same folder database.py uses
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _file_path(name):
    return os.path.join(DATA_DIR, f"{name}.json")

def _load(name):
    path = _file_path(name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def _save(name, data):
    path = _file_path(name)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════
# TASTE PROFILE STRUCTURE
# ═══════════════════════════════════════════════════════════════

def _default_profile():
    return {
        "artists":       {},
        "genres":        {},
        "languages":     {},
        "moods":         {},
        "tempo":         {},
        "liked_songs":   [],
        "skipped_songs": [],
        "played_songs":  {},
        "total_plays":   0,
        "total_skips":   0,
        "last_updated":  None,
    }


def get_taste_profile(user_id: str) -> dict:
    data = _load("taste_profiles")
    return data.get(user_id, _default_profile())


def _save_profile(user_id: str, profile: dict):
    data = _load("taste_profiles")
    profile["last_updated"] = datetime.now(timezone.utc).isoformat()
    data[user_id] = profile
    _save("taste_profiles", data)


# ═══════════════════════════════════════════════════════════════
# EVENT HANDLERS
# ═══════════════════════════════════════════════════════════════

def on_song_played(user_id: str, song: dict, listen_seconds: int = 60):
    profile  = get_taste_profile(user_id)
    song_id  = song.get("song_id") or song.get("id", "")
    artist   = song.get("artist", "Unknown")
    genre    = song.get("genre", "")
    language = song.get("language", "")
    mood     = song.get("mood", "")
    tempo    = song.get("tempo", "")
    duration = int(song.get("duration") or 180)

    real_play = listen_seconds >= max(30, duration * 0.30)

    if real_play:
        profile["total_plays"] += 1
        profile["artists"][artist] = profile["artists"].get(artist, 0) + 1
        if genre:
            profile["genres"][genre] = profile["genres"].get(genre, 0) + 1
        if language:
            profile["languages"][language] = profile["languages"].get(language, 0) + 1
        if mood:
            profile["moods"][mood] = profile["moods"].get(mood, 0) + 1
        if tempo:
            profile["tempo"][tempo] = profile["tempo"].get(tempo, 0) + 1
        if song_id:
            profile["played_songs"][song_id] = profile["played_songs"].get(song_id, 0) + 1

    _save_profile(user_id, profile)
    return {"success": True, "real_play": real_play}


def on_song_skipped(user_id: str, song: dict, listen_seconds: int = 5):
    profile = get_taste_profile(user_id)
    song_id = song.get("song_id") or song.get("id", "")
    profile["total_skips"] += 1

    if listen_seconds < 10 and song_id:
        skipped = profile.get("skipped_songs", [])
        if song_id not in skipped:
            skipped.append(song_id)
        profile["skipped_songs"] = skipped[-200:]

    _save_profile(user_id, profile)
    return {"success": True}


def on_song_liked(user_id: str, song: dict):
    profile  = get_taste_profile(user_id)
    song_id  = song.get("song_id") or song.get("id", "")
    artist   = song.get("artist", "Unknown")
    genre    = song.get("genre", "")
    language = song.get("language", "")
    mood     = song.get("mood", "")
    tempo    = song.get("tempo", "")

    LIKE_BOOST = 5

    profile["artists"][artist] = profile["artists"].get(artist, 0) + LIKE_BOOST
    if genre:
        profile["genres"][genre] = profile["genres"].get(genre, 0) + LIKE_BOOST
    if language:
        profile["languages"][language] = profile["languages"].get(language, 0) + LIKE_BOOST
    if mood:
        profile["moods"][mood] = profile["moods"].get(mood, 0) + LIKE_BOOST
    if tempo:
        profile["tempo"][tempo] = profile["tempo"].get(tempo, 0) + LIKE_BOOST

    liked = profile.get("liked_songs", [])
    if song_id and song_id not in liked:
        liked.append(song_id)
    profile["liked_songs"] = liked[-500:]

    _save_profile(user_id, profile)
    return {"success": True}


# ═══════════════════════════════════════════════════════════════
# INSIGHT HELPERS
# ═══════════════════════════════════════════════════════════════

def get_top_artists(user_id: str, limit: int = 10) -> list:
    profile = get_taste_profile(user_id)
    artists = profile.get("artists", {})
    return sorted(artists.items(), key=lambda x: x[1], reverse=True)[:limit]


def get_top_genres(user_id: str, limit: int = 5) -> list:
    profile = get_taste_profile(user_id)
    genres  = profile.get("genres", {})
    return sorted(genres.items(), key=lambda x: x[1], reverse=True)[:limit]


def get_top_languages(user_id: str, limit: int = 5) -> list:
    profile  = get_taste_profile(user_id)
    langs    = profile.get("languages", {})
    return sorted(langs.items(), key=lambda x: x[1], reverse=True)[:limit]


def get_preferred_mood(user_id: str) -> str:
    profile = get_taste_profile(user_id)
    moods   = profile.get("moods", {})
    if not moods:
        return "happy"
    return max(moods, key=moods.get)


def get_preferred_tempo(user_id: str) -> str:
    profile = get_taste_profile(user_id)
    tempos  = profile.get("tempo", {})
    if not tempos:
        return "medium"
    return max(tempos, key=tempos.get)


def get_disliked_songs(user_id: str) -> list:
    profile = get_taste_profile(user_id)
    return profile.get("skipped_songs", [])


def get_liked_songs(user_id: str) -> list:
    profile = get_taste_profile(user_id)
    return profile.get("liked_songs", [])


def get_full_taste_summary(user_id: str) -> dict:
    return {
        "top_artists":     get_top_artists(user_id, 10),
        "top_genres":      get_top_genres(user_id, 5),
        "top_languages":   get_top_languages(user_id, 3),
        "preferred_mood":  get_preferred_mood(user_id),
        "preferred_tempo": get_preferred_tempo(user_id),
        "liked_songs":     get_liked_songs(user_id),
        "disliked_songs":  get_disliked_songs(user_id),
        "total_plays":     get_taste_profile(user_id).get("total_plays", 0),
    }
    
