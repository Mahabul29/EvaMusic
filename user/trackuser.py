"""
EvaMusic — User Taste & Play Count Tracker
Tracks:
  • Song play counts → auto-adds to "Your Usuals" if played > 5 times
  • Artist play counts → auto-adds to "Trending Artists" if played > 5 times
  • Full taste summary for suggestions
"""

import database as db
from collections import Counter

# ═══════════════════════════════════════════════════════════════
# PLAY COUNT THRESHOLDS
# ═══════════════════════════════════════════════════════════════

SONG_PLAY_THRESHOLD = 5    # Plays needed to auto-add to "Your Usuals"
ARTIST_PLAY_THRESHOLD = 5  # Plays needed to auto-add to "Trending Artists"


# ═══════════════════════════════════════════════════════════════
# RECORD A PLAY
# ═══════════════════════════════════════════════════════════════

def record_play(user_id: str, song_data: dict):
    """
    Call this EVERY TIME a song is played.
    Increments play count. If count >= threshold, auto-adds to Usuals/Trending.
    """
    song_id = song_data.get("song_id") or song_data.get("id", "")
    artist = song_data.get("artist", "Unknown")
    title = song_data.get("title", "Unknown")
    language = song_data.get("language", "hindi")

    if not song_id:
        return

    # ── Increment song play count ──
    plays = db._load("play_counts")
    if user_id not in plays:
        plays[user_id] = {}

    if song_id not in plays[user_id]:
        plays[user_id][song_id] = {
            "count": 0,
            "title": title,
            "artist": artist,
            "language": language,
            "image_url": song_data.get("image_url", "") or song_data.get("image", ""),
        }

    plays[user_id][song_id]["count"] += 1
    count = plays[user_id][song_id]["count"]
    db._save("play_counts", plays)

    # ── Auto-add to "Your Usuals" if threshold reached ──
    if count == SONG_PLAY_THRESHOLD:
        print(f"[TRACKER] Song '{title}' reached {count} plays → Added to Your Usuals!")
        _add_to_usuals(user_id, plays[user_id][song_id])

    # ── Increment artist play count ──
    artist_names = [a.strip() for a in str(artist).replace("&", ",").split(",") if a.strip()]

    artist_plays = db._load("artist_play_counts")
    if user_id not in artist_plays:
        artist_plays[user_id] = {}

    for artist_name in artist_names:
        key = artist_name.lower()
        if key not in artist_plays[user_id]:
            artist_plays[user_id][key] = {
                "count": 0,
                "name": artist_name,
                "image_url": song_data.get("image_url", "") or song_data.get("image", ""),
            }

        artist_plays[user_id][key]["count"] += 1
        artist_count = artist_plays[user_id][key]["count"]

        # Auto-add to "Trending Artists" if threshold reached
        if artist_count == ARTIST_PLAY_THRESHOLD:
            print(f"[TRACKER] Artist '{artist_name}' reached {artist_count} plays → Added to Trending Artists!")
            _add_to_trending_artists(user_id, artist_plays[user_id][key])

    db._save("artist_play_counts", artist_plays)

    # ── Also update taste profile ──
    on_song_liked(user_id, song_data)


# ═══════════════════════════════════════════════════════════════
# AUTO-ADD HELPERS
# ═══════════════════════════════════════════════════════════════

def _add_to_usuals(user_id: str, song_info: dict):
    """Add a song to user's "Your Usuals" collection."""
    usuals = db._load("usuals")
    if user_id not in usuals:
        usuals[user_id] = []

    existing_ids = {s.get("song_id") for s in usuals[user_id]}
    song_id = song_info.get("song_id", "")

    if song_id not in existing_ids:
        usuals[user_id].append({
            "song_id":   song_id,
            "title":     song_info.get("title", "Unknown"),
            "artist":    song_info.get("artist", "Unknown"),
            "image_url": song_info.get("image_url", ""),
            "language":  song_info.get("language", "hindi"),
            "added_at":  __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "play_count": song_info.get("count", 5),
        })
        db._save("usuals", usuals)


def _add_to_trending_artists(user_id: str, artist_info: dict):
    """Add an artist to user's "Trending Artists" collection."""
    trending = db._load("trending_artists")
    if user_id not in trending:
        trending[user_id] = []

    existing_ids = {a.get("name", "").lower() for a in trending[user_id]}
    artist_name = artist_info.get("name", "").lower()

    if artist_name not in existing_ids:
        trending[user_id].append({
            "name":      artist_info.get("name", "Unknown"),
            "image_url": artist_info.get("image_url", ""),
            "added_at":  __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "play_count": artist_info.get("count", 5),
        })
        db._save("trending_artists", trending)


# ═══════════════════════════════════════════════════════════════
# GET "YOUR USUALS" (songs played > 5 times)
# ═══════════════════════════════════════════════════════════════

def get_usuals(user_id: str, limit: int = 10):
    """Get songs that user has played > 5 times."""
    usuals = db._load("usuals")
    user_usuals = usuals.get(user_id, [])
    user_usuals.sort(key=lambda x: x.get("play_count", 0), reverse=True)
    return user_usuals[:limit]


def get_trending_artists_for_user(user_id: str, limit: int = 10):
    """Get artists that user has played > 5 times."""
    trending = db._load("trending_artists")
    user_trending = trending.get(user_id, [])
    user_trending.sort(key=lambda x: x.get("play_count", 0), reverse=True)
    return user_trending[:limit]


# ═══════════════════════════════════════════════════════════════
# GET TOP PLAYED (for taste profile)
# ═══════════════════════════════════════════════════════════════

def get_top_played_songs(user_id: str, limit: int = 20):
    """Get most played songs by play count."""
    plays = db._load("play_counts")
    user_plays = plays.get(user_id, {})
    sorted_songs = sorted(
        user_plays.values(),
        key=lambda x: x.get("count", 0),
        reverse=True
    )
    return sorted_songs[:limit]


def get_top_played_artists(user_id: str, limit: int = 10):
    """Get most played artists by play count."""
    artist_plays = db._load("artist_play_counts")
    user_artists = artist_plays.get(user_id, {})
    sorted_artists = sorted(
        user_artists.values(),
        key=lambda x: x.get("count", 0),
        reverse=True
    )
    return sorted_artists[:limit]


# ═══════════════════════════════════════════════════════════════
# FULL TASTE SUMMARY (updated with play counts)
# ═══════════════════════════════════════════════════════════════

def get_full_taste_summary(user_id: str) -> dict:
    """Complete taste profile including play counts."""
    taste = _get_base_taste(user_id)

    top_songs        = get_top_played_songs(user_id, 10)
    top_artists      = get_top_played_artists(user_id, 10)
    usuals           = get_usuals(user_id, 10)
    trending_artists = get_trending_artists_for_user(user_id, 10)

    taste["top_played_songs"]    = top_songs
    taste["top_played_artists"]  = top_artists
    taste["usuals"]              = usuals
    taste["trending_artists"]    = trending_artists
    taste["total_plays"]         = sum(s.get("count", 0) for s in top_songs)

    return taste


def _get_base_taste(user_id: str) -> dict:
    """Get base taste from existing database."""
    try:
        favorites = db.get_user_favorites(user_id)
        history   = db.get_recently_played(user_id, 50)

        artist_counter = Counter()
        genre_counter  = Counter()
        lang_counter   = Counter()

        for item in favorites + history:
            artist = item.get("artist", "")
            for a in str(artist).replace("&", ",").split(","):
                a = a.strip()
                if a:
                    artist_counter[a] += 1

            genre = item.get("genre", "")
            if genre:
                genre_counter[genre] += 1

            lang = item.get("language", "hindi")
            if lang:
                lang_counter[lang] += 1

        return {
            "top_artists":    artist_counter.most_common(10),
            "top_genres":     genre_counter.most_common(5),
            "top_languages":  lang_counter.most_common(5),
            "total_plays":    len(history),
            "liked_songs":    [f.get("song_id") for f in favorites],
            "disliked_songs": [],
        }
    except Exception as e:
        print(f"[TASTE ERROR] {e}")
        return {
            "top_artists":    [],
            "top_genres":     [],
            "top_languages":  [],
            "total_plays":    0,
            "liked_songs":    [],
            "disliked_songs": [],
        }


# ═══════════════════════════════════════════════════════════════
# SKIP & PLAYED TRACKING
# ═══════════════════════════════════════════════════════════════

def on_song_skipped(user_id: str, song_data: dict, listen_seconds: int = 3):
    """
    Called when a user skips a song.
    Short listens (< 10s) are logged but don't count as a play.
    """
    if not user_id:
        return

    song_id = song_data.get("song_id") or song_data.get("id", "")
    if not song_id:
        return

    skips = db._load("song_skips")
    if user_id not in skips:
        skips[user_id] = {}

    if song_id not in skips[user_id]:
        skips[user_id][song_id] = {
            "count":      0,
            "title":      song_data.get("title", "Unknown"),
            "artist":     song_data.get("artist", "Unknown"),
        }

    skips[user_id][song_id]["count"] += 1
    skips[user_id][song_id]["last_listen_seconds"] = listen_seconds
    db._save("song_skips", skips)

    print(f"[TRACKER] Skipped '{song_data.get('title', song_id)}' after {listen_seconds}s "
          f"(total skips: {skips[user_id][song_id]['count']})")


def on_song_played(user_id: str, song_data: dict, listen_seconds: int = 60):
    """
    Called when a song finishes or plays long enough to count.
    Delegates to record_play so all play-count logic stays in one place.
    """
    if not user_id:
        return

    # Only count as a real play if the user listened for at least 15 seconds
    if listen_seconds < 15:
        return

    record_play(user_id, song_data)


# ═══════════════════════════════════════════════════════════════
# LEGACY: Keep old functions working
# ═══════════════════════════════════════════════════════════════

def on_song_liked(user_id: str, song_data: dict):
    """Legacy function - now handled by record_play."""
    pass  # record_play handles everything now


def get_liked_songs(user_id: str):
    """Get liked song IDs."""
    try:
        favorites = db.get_user_favorites(user_id)
        return [f.get("song_id") for f in favorites]
    except:
        return []


def get_disliked_songs(user_id: str):
    """Get disliked song IDs."""
    return []


def get_preferred_mood(user_id: str):
    """Get user's preferred mood."""
    return "happy"
  
