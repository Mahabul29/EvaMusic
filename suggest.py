"""
EvaMusic — Song Suggestion Engine
Generates personalised song suggestions based on:
  • What the user has liked / played most
  • Their top genres, artists, moods & languages
  • Songs they have NOT skipped
"""

import random

from user.trackuser import (
    get_full_taste_summary,
    get_disliked_songs,
    get_liked_songs,
    get_preferred_mood,
)
import database as db


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _score_song(song: dict, taste: dict) -> float:
    score = 0.0
    song_artist   = (song.get("artist") or "").lower()
    song_genre    = (song.get("genre") or "").lower()
    song_language = (song.get("language") or "").lower()
    song_mood     = (song.get("mood") or "").lower()
    song_tempo    = (song.get("tempo") or "").lower()
    song_id       = song.get("song_id") or song.get("id", "")

    if song_id in taste.get("disliked_songs", []):
        return -999.0

    if song_id in taste.get("liked_songs", []):
        score -= 2.0

    for artist, weight in taste.get("top_artists", []):
        if artist.lower() in song_artist or song_artist in artist.lower():
            score += weight * 2.0
            break

    for genre, weight in taste.get("top_genres", []):
        if genre.lower() in song_genre:
            score += weight * 1.5
            break

    for lang, weight in taste.get("top_languages", []):
        if lang.lower() == song_language:
            score += weight * 1.2
            break

    if taste.get("preferred_mood") and taste["preferred_mood"].lower() == song_mood:
        score += 3.0

    if taste.get("preferred_tempo") and taste["preferred_tempo"].lower() == song_tempo:
        score += 2.0

    return score


def _deduplicate(songs: list) -> list:
    seen = set()
    out  = []
    for s in songs:
        sid = s.get("song_id") or s.get("id", "")
        if sid and sid not in seen:
            seen.add(sid)
            out.append(s)
    return out


# ═══════════════════════════════════════════════════════════════
# MAIN SUGGESTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_suggestions_for_user(user_id: str, candidate_songs: list, limit: int = 20) -> list:
    taste = get_full_taste_summary(user_id)

    if taste["total_plays"] == 0:
        return candidate_songs[:limit]

    scored = []
    for song in candidate_songs:
        s = _score_song(song, taste)
        scored.append((s, song))

    scored.sort(key=lambda x: (x[0], random.random()), reverse=True)

    result = [song for _, song in scored]
    result = _deduplicate(result)
    return result[:limit]


def get_because_you_liked(user_id: str, all_songs: list, limit: int = 10) -> list:
    liked_ids = set(get_liked_songs(user_id))
    taste     = get_full_taste_summary(user_id)

    if not liked_ids or taste["total_plays"] == 0:
        return []

    disliked = set(get_disliked_songs(user_id))
    candidates = [
        s for s in all_songs
        if (s.get("song_id") or s.get("id", "")) not in liked_ids
        and (s.get("song_id") or s.get("id", "")) not in disliked
    ]

    return get_suggestions_for_user(user_id, candidates, limit)


def get_mood_mix(user_id: str, all_songs: list, mood: str = None, limit: int = 10) -> list:
    target_mood = mood or get_preferred_mood(user_id)

    mood_songs = [
        s for s in all_songs
        if (s.get("mood") or "").lower() == target_mood.lower()
    ]

    if not mood_songs:
        return get_suggestions_for_user(user_id, all_songs, limit)

    return get_suggestions_for_user(user_id, mood_songs, limit)


def get_artist_radio(user_id: str, artist_name: str, all_songs: list, limit: int = 15) -> list:
    artist_songs = [
        s for s in all_songs
        if artist_name.lower() in (s.get("artist") or "").lower()
    ]
    return get_suggestions_for_user(user_id, artist_songs, limit)


def get_fresh_picks(user_id: str, all_songs: list, limit: int = 10) -> list:
    taste    = get_full_taste_summary(user_id)
    known    = set(taste.get("liked_songs", []))
    disliked = set(taste.get("disliked_songs", []))

    fresh = [
        s for s in all_songs
        if (s.get("song_id") or s.get("id", "")) not in known
        and (s.get("song_id") or s.get("id", "")) not in disliked
    ]

    return get_suggestions_for_user(user_id, fresh, limit)


def build_homepage_sections(user_id: str, trending_songs: list) -> dict:
    taste       = get_full_taste_summary(user_id)
    is_new_user = taste["total_plays"] < 5
    sections    = {}

    if is_new_user:
        sections["trending"]  = trending_songs[:12]
        sections["new_user"]  = True
    else:
        top_artists = [a for a, _ in taste["top_artists"][:3]]

        sections["for_you"]           = get_suggestions_for_user(user_id, trending_songs, 12)
        sections["because_you_liked"] = get_because_you_liked(user_id, trending_songs, 8)
        sections["mood_mix"]          = get_mood_mix(user_id, trending_songs, limit=8)
        sections["fresh_picks"]       = get_fresh_picks(user_id, trending_songs, 8)
        sections["top_artist"]        = top_artists[0] if top_artists else None
        sections["artist_radio"]      = (
            get_artist_radio(user_id, top_artists[0], trending_songs, 8)
            if top_artists else []
        )
        sections["new_user"] = False

    return sections
  
