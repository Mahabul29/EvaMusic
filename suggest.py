"""
EvaMusic — Song Suggestion Engine
Generates personalised song suggestions based on:
  • What the user has liked / played most
  • Their top genres, artists, moods & languages
  • Songs they have NOT skipped
  • Collaborative: what similar users are playing (basic version)
"""

import random
from datetime import datetime, timezone

# Internal imports (same package)
from user.trackuser import (
    get_full_taste_summary,
    get_disliked_songs,
    get_liked_songs,
)
import database as db


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _score_song(song: dict, taste: dict) -> float:
    """
    Score a candidate song against the user's taste profile.
    Higher score = better match.
    """
    score = 0.0
    song_artist   = (song.get("artist") or "").lower()
    song_genre    = (song.get("genre") or "").lower()
    song_language = (song.get("language") or "").lower()
    song_mood     = (song.get("mood") or "").lower()
    song_tempo    = (song.get("tempo") or "").lower()
    song_id       = song.get("song_id") or song.get("id", "")

    # Hard skip — user dislikes this song
    if song_id in taste.get("disliked_songs", []):
        return -999.0

    # Already in liked list — still show but lower priority (they know it)
    if song_id in taste.get("liked_songs", []):
        score -= 2.0

    # Artist match
    for artist, weight in taste.get("top_artists", []):
        if artist.lower() in song_artist or song_artist in artist.lower():
            score += weight * 2.0
            break

    # Genre match
    for genre, weight in taste.get("top_genres", []):
        if genre.lower() in song_genre:
            score += weight * 1.5
            break

    # Language match
    for lang, weight in taste.get("top_languages", []):
        if lang.lower() == song_language:
            score += weight * 1.2
            break

    # Mood match
    if taste.get("preferred_mood") and taste["preferred_mood"].lower() == song_mood:
        score += 3.0

    # Tempo match
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
    """
    Rank `candidate_songs` by how well they match the user's taste.
    `candidate_songs` comes from the JioSaavn API (trending / search results).

    Returns a sorted list of up to `limit` songs.
    """
    taste = get_full_taste_summary(user_id)

    # If the user is brand new (no plays yet), just return trending
    if taste["total_plays"] == 0:
        return candidate_songs[:limit]

    scored = []
    for song in candidate_songs:
        s = _score_song(song, taste)
        scored.append((s, song))

    # Sort by score descending, break ties randomly
    scored.sort(key=lambda x: (x[0], random.random()), reverse=True)

    result = [song for _, song in scored]
    result = _deduplicate(result)
    return result[:limit]


def get_because_you_liked(user_id: str, all_songs: list, limit: int = 10) -> list:
    """
    Returns songs that are similar to what the user has liked.
    Used for the 'Because you liked …' section on the homepage.
    """
    liked_ids = set(get_liked_songs(user_id))
    taste     = get_full_taste_summary(user_id)

    if not liked_ids or taste["total_plays"] == 0:
        return []

    # Filter out songs they already know and disliked
    disliked = set(get_disliked_songs(user_id))
    candidates = [
        s for s in all_songs
        if (s.get("song_id") or s.get("id", "")) not in liked_ids
        and (s.get("song_id") or s.get("id", "")) not in disliked
    ]

    return get_suggestions_for_user(user_id, candidates, limit)


def get_mood_mix(user_id: str, all_songs: list, mood: str = None, limit: int = 10) -> list:
    """
    Return songs matching a specific mood (or the user's preferred mood).
    """
    from user.trackuser import get_preferred_mood
    target_mood = mood or get_preferred_mood(user_id)

    mood_songs = [
        s for s in all_songs
        if (s.get("mood") or "").lower() == target_mood.lower()
    ]

    if not mood_songs:
        # Fall back to general suggestions
        return get_suggestions_for_user(user_id, all_songs, limit)

    return get_suggestions_for_user(user_id, mood_songs, limit)


def get_artist_radio(user_id: str, artist_name: str, all_songs: list, limit: int = 15) -> list:
    """
    Songs by a specific artist, sorted by user preference signals.
    """
    artist_songs = [
        s for s in all_songs
        if artist_name.lower() in (s.get("artist") or "").lower()
    ]
    return get_suggestions_for_user(user_id, artist_songs, limit)


def get_fresh_picks(user_id: str, all_songs: list, limit: int = 10) -> list:
    """
    Songs the user has NEVER played or liked — discovery mode.
    """
    taste    = get_full_taste_summary(user_id)
    known    = set(taste.get("liked_songs", []))
    disliked = set(taste.get("disliked_songs", []))

    fresh = [
        s for s in all_songs
        if (s.get("song_id") or s.get("id", "")) not in known
        and (s.get("song_id") or s.get("id", "")) not in disliked
    ]

    # Light scoring still applied so freshness meets taste
    return get_suggestions_for_user(user_id, fresh, limit)


def build_homepage_sections(user_id: str, trending_songs: list) -> dict:
    """
    Build all suggestion sections for the homepage in one call.
    Returns a dict of labelled song lists ready to pass to the template.
    """
    taste = get_full_taste_summary(user_id)
    is_new_user = taste["total_plays"] < 5

    sections = {}

    if is_new_user:
        # New user — show trending only
        sections["trending"]       = trending_songs[:12]
        sections["new_user"]       = True
    else:
        top_artists = [a for a, _ in taste["top_artists"][:3]]

        sections["for_you"]        = get_suggestions_for_user(user_id, trending_songs, 12)
        sections["because_you_liked"] = get_because_you_liked(user_id, trending_songs, 8)
        sections["mood_mix"]       = get_mood_mix(user_id, trending_songs, limit=8)
        sections["fresh_picks"]    = get_fresh_picks(user_id, trending_songs, 8)
        sections["top_artist"]     = top_artists[0] if top_artists else None
        sections["artist_radio"]   = (
            get_artist_radio(user_id, top_artists[0], trending_songs, 8)
            if top_artists else []
        )
        sections["new_user"]       = False

    return sections
