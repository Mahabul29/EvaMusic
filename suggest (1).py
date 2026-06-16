"""
EvaMusic — Song Suggestion Engine (COMPLETE WORKING VERSION)
Generates personalised song suggestions based on user behavior.
"""

import random
from user.trackuser import (
    get_full_taste_summary,
    get_disliked_songs,
    get_liked_songs,
    get_preferred_mood,
)
import database as db


def _score_song(song, taste):
    score = 0.0
    song_artist = (song.get("artist") or song.get("primaryArtists") or song.get("singers") or "").lower()
    song_genre = (song.get("genre") or "").lower()
    song_language = (song.get("language") or "hindi").lower()
    song_mood = (song.get("mood") or "").lower()
    song_tempo = (song.get("tempo") or "").lower()
    song_id = song.get("song_id") or song.get("id") or song.get("songId") or ""

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


def _deduplicate(songs):
    seen = set()
    out = []
    for s in songs:
        sid = s.get("song_id") or s.get("id") or s.get("songId") or ""
        if sid and sid not in seen:
            seen.add(sid)
            out.append(s)
    return out


def get_suggestions_for_user(user_id, candidate_songs, limit=20):
    """Get personalized suggestions. New users get random shuffle."""
    taste = get_full_taste_summary(user_id)

    # NEW USER: no plays, no likes → random shuffle
    if taste["total_plays"] == 0 and not taste.get("liked_songs"):
        shuffled = candidate_songs[:]
        random.shuffle(shuffled)
        return _deduplicate(shuffled)[:limit]

    # EXISTING USER: score by taste
    scored = []
    for song in candidate_songs:
        s = _score_song(song, taste)
        scored.append((s, song))

    scored.sort(key=lambda x: (x[0], random.random()), reverse=True)
    result = [song for _, song in scored]
    return _deduplicate(result)[:limit]


def get_similar_songs(song_data, candidate_songs, limit=10):
    """Find songs similar to given song (same artist, language, genre, mood)."""
    target_artist = (song_data.get("artist") or song_data.get("primaryArtists") or song_data.get("singers") or "").lower()
    target_lang = (song_data.get("language") or "hindi").lower()
    target_genre = (song_data.get("genre") or "").lower()
    target_mood = (song_data.get("mood") or "").lower()
    target_id = song_data.get("id") or song_data.get("song_id") or song_data.get("songId") or ""

    scored = []
    for s in candidate_songs:
        sid = s.get("id") or s.get("song_id") or s.get("songId") or ""
        if sid == target_id:
            continue

        score = 0.0
        s_artist = (s.get("artist") or s.get("primaryArtists") or s.get("singers") or "").lower()
        s_lang = (s.get("language") or "hindi").lower()
        s_genre = (s.get("genre") or "").lower()
        s_mood = (s.get("mood") or "").lower()

        # Same artist = strongest match (10 points)
        if target_artist and target_artist in s_artist:
            score += 10.0

        # Same language (3 points)
        if target_lang and target_lang == s_lang:
            score += 3.0

        # Same genre (2 points)
        if target_genre and target_genre == s_genre:
            score += 2.0

        # Same mood (2 points)
        if target_mood and target_mood == s_mood:
            score += 2.0

        scored.append((score, s))

    scored.sort(key=lambda x: (x[0], random.random()), reverse=True)
    result = [song for _, song in scored]
    return _deduplicate(result)[:limit]


def get_similar_artists(artist_name, candidate_artists, limit=10):
    """Get artists similar to given artist."""
    if not candidate_artists:
        return []

    shuffled = candidate_artists[:]
    random.shuffle(shuffled)

    # Filter out exact same artist name
    result = [a for a in shuffled if (a.get("name") or "").lower() != artist_name.lower()]
    if not result:
        result = shuffled

    return result[:limit]


def get_because_you_liked(user_id, all_songs, limit=10):
    """Get songs based on user's taste (not just liked songs)."""
    taste = get_full_taste_summary(user_id)

    # Show for ANY user with plays OR likes
    if taste["total_plays"] == 0 and not taste.get("liked_songs"):
        return []

    liked_ids = set(get_liked_songs(user_id))
    disliked = set(get_disliked_songs(user_id))

    candidates = [
        s for s in all_songs
        if (s.get("song_id") or s.get("id") or s.get("songId") or "") not in liked_ids
        and (s.get("song_id") or s.get("id") or s.get("songId") or "") not in disliked
    ]

    return get_suggestions_for_user(user_id, candidates, limit)


def get_mood_mix(user_id, all_songs, mood=None, limit=10):
    target_mood = mood or get_preferred_mood(user_id)

    mood_songs = [
        s for s in all_songs
        if (s.get("mood") or "").lower() == target_mood.lower()
    ]

    if not mood_songs:
        return get_suggestions_for_user(user_id, all_songs, limit)

    return get_suggestions_for_user(user_id, mood_songs, limit)


def get_artist_radio(user_id, artist_name, all_songs, limit=15):
    artist_songs = [
        s for s in all_songs
        if artist_name.lower() in (s.get("artist") or s.get("primaryArtists") or s.get("singers") or "").lower()
    ]
    return get_suggestions_for_user(user_id, artist_songs, limit)


def get_fresh_picks(user_id, all_songs, limit=10):
    taste = get_full_taste_summary(user_id)
    known = set(taste.get("liked_songs", []))
    disliked = set(taste.get("disliked_songs", []))
    played = set()

    try:
        history = db.get_recently_played(user_id, 50)
        played = {h.get("song_id") or h.get("id") or "" for h in history}
    except:
        pass

    fresh = [
        s for s in all_songs
        if (s.get("song_id") or s.get("id") or s.get("songId") or "") not in known
        and (s.get("song_id") or s.get("id") or s.get("songId") or "") not in disliked
        and (s.get("song_id") or s.get("id") or s.get("songId") or "") not in played
    ]

    return get_suggestions_for_user(user_id, fresh, limit)


def build_homepage_sections(user_id, trending_songs):
    """Build all homepage sections."""
    taste = get_full_taste_summary(user_id)
    is_new_user = taste["total_plays"] < 5 and not taste.get("liked_songs")
    sections = {}

    if is_new_user:
        # NEW USER: random trending songs
        shuffled = trending_songs[:]
        random.shuffle(shuffled)
        sections["trending"] = shuffled[:12]
        sections["for_you"] = shuffled[:12]
        sections["new_user"] = True
    else:
        # EXISTING USER: personalized
        top_artists = [a for a, _ in taste.get("top_artists", [])[:3]]

        sections["for_you"] = get_suggestions_for_user(user_id, trending_songs, 12)
        sections["because_you_liked"] = get_because_you_liked(user_id, trending_songs, 8)
        sections["mood_mix"] = get_mood_mix(user_id, trending_songs, limit=8)
        sections["fresh_picks"] = get_fresh_picks(user_id, trending_songs, 8)
        sections["top_artist"] = top_artists[0] if top_artists else None
        sections["artist_radio"] = (
            get_artist_radio(user_id, top_artists[0], trending_songs, 8)
            if top_artists else []
        )
        sections["new_user"] = False

    return sections
