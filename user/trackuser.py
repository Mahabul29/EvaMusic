"""
EvaMusic — User Taste & Play Count Tracker (FIXED)
Tracks:
  • Song play counts → auto-adds to "Your Usuals" if played > 5 times
  • Artist play counts → auto-adds to "Trending Artists" if played > 5 times
  • Full taste summary for suggestions
  • NOW: taste profile updates when song is played
"""

import database as db
from collections import Counter

SONG_PLAY_THRESHOLD = 5
ARTIST_PLAY_THRESHOLD = 5


def record_play(user_id: str, song_data: dict):
    """Call this EVERY TIME a song is played."""
    song_id = song_data.get("song_id") or song_data.get("id") or song_data.get("songId") or ""
    artist = song_data.get("artist") or song_data.get("primaryArtists") or song_data.get("singers") or "Unknown"
    title = song_data.get("title") or song_data.get("name") or song_data.get("song") or "Unknown"
    language = song_data.get("language") or "hindi"
    image_url = song_data.get("image_url") or song_data.get("image") or song_data.get("thumbnail") or ""

    if not song_id:
        return

    # Increment song play count
    plays = db._load("play_counts")
    if user_id not in plays:
        plays[user_id] = {}

    if song_id not in plays[user_id]:
        plays[user_id][song_id] = {
            "count": 0,
            "title": title,
            "artist": artist,
            "language": language,
            "image_url": image_url,
        }

    plays[user_id][song_id]["count"] += 1
    count = plays[user_id][song_id]["count"]
    db._save("play_counts", plays)

    # Auto-add to "Your Usuals" if threshold reached
    if count == SONG_PLAY_THRESHOLD:
        print(f"[TRACKER] Song '{title}' reached {count} plays → Added to Your Usuals!")
        _add_to_usuals(user_id, plays[user_id][song_id])

    # Increment artist play count
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
                "image_url": image_url,
            }

        artist_plays[user_id][key]["count"] += 1
        artist_count = artist_plays[user_id][key]["count"]

        if artist_count == ARTIST_PLAY_THRESHOLD:
            print(f"[TRACKER] Artist '{artist_name}' reached {artist_count} plays → Added to Trending Artists!")
            _add_to_trending_artists(user_id, artist_plays[user_id][key])

    db._save("artist_play_counts", artist_plays)

    # NOW FIXED: Update taste profile when song is played
    _update_taste_profile(user_id, song_data)


def _update_taste_profile(user_id: str, song_data: dict):
    """Update user taste profile with song metadata."""
    taste = db._load("taste_profiles")
    if user_id not in taste:
        taste[user_id] = {
            "artists": {},
            "genres": {},
            "languages": {},
            "moods": {},
            "tempos": {},
            "updated_at": None,
        }

    artist = song_data.get("artist") or song_data.get("primaryArtists") or song_data.get("singers") or "Unknown"
    genre = song_data.get("genre") or ""
    language = song_data.get("language") or "hindi"
    mood = song_data.get("mood") or ""
    tempo = song_data.get("tempo") or ""

    for a in str(artist).replace("&", ",").split(","):
        a = a.strip()
        if a:
            taste[user_id]["artists"][a] = taste[user_id]["artists"].get(a, 0) + 1

    if genre:
        taste[user_id]["genres"][genre] = taste[user_id]["genres"].get(genre, 0) + 1

    if language:
        taste[user_id]["languages"][language] = taste[user_id]["languages"].get(language, 0) + 1

    if mood:
        taste[user_id]["moods"][mood] = taste[user_id]["moods"].get(mood, 0) + 1

    if tempo:
        taste[user_id]["tempos"][tempo] = taste[user_id]["tempos"].get(tempo, 0) + 1

    from datetime import datetime, timezone
    taste[user_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    db._save("taste_profiles", taste)


def _add_to_usuals(user_id: str, song_info: dict):
    usuals = db._load("usuals")
    if user_id not in usuals:
        usuals[user_id] = []

    existing_ids = {s.get("song_id") for s in usuals[user_id]}
    song_id = song_info.get("song_id") or song_info.get("id") or ""

    if song_id not in existing_ids:
        usuals[user_id].append({
            "song_id": song_id,
            "title": song_info.get("title", "Unknown"),
            "artist": song_info.get("artist", "Unknown"),
            "image_url": song_info.get("image_url", ""),
            "language": song_info.get("language", "hindi"),
            "added_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "play_count": song_info.get("count", 5),
        })
        db._save("usuals", usuals)


def _add_to_trending_artists(user_id: str, artist_info: dict):
    trending = db._load("trending_artists")
    if user_id not in trending:
        trending[user_id] = []

    existing_ids = {a.get("name", "").lower() for a in trending[user_id]}
    artist_name = artist_info.get("name", "").lower()

    if artist_name not in existing_ids:
        trending[user_id].append({
            "name": artist_info.get("name", "Unknown"),
            "image_url": artist_info.get("image_url", ""),
            "added_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "play_count": artist_info.get("count", 5),
        })
        db._save("trending_artists", trending)


def get_usuals(user_id: str, limit: int = 10):
    usuals = db._load("usuals")
    user_usuals = usuals.get(user_id, [])
    user_usuals.sort(key=lambda x: x.get("play_count", 0), reverse=True)
    return user_usuals[:limit]


def get_trending_artists_for_user(user_id: str, limit: int = 10):
    trending = db._load("trending_artists")
    user_trending = trending.get(user_id, [])
    user_trending.sort(key=lambda x: x.get("play_count", 0), reverse=True)
    return user_trending[:limit]


def get_top_played_songs(user_id: str, limit: int = 20):
    plays = db._load("play_counts")
    user_plays = plays.get(user_id, {})
    sorted_songs = sorted(
        user_plays.values(),
        key=lambda x: x.get("count", 0),
        reverse=True
    )
    return sorted_songs[:limit]


def get_top_played_artists(user_id: str, limit: int = 10):
    artist_plays = db._load("artist_play_counts")
    user_artists = artist_plays.get(user_id, {})
    sorted_artists = sorted(
        user_artists.values(),
        key=lambda x: x.get("count", 0),
        reverse=True
    )
    return sorted_artists[:limit]


def get_full_taste_summary(user_id: str) -> dict:
    taste = _get_base_taste(user_id)

    top_songs = get_top_played_songs(user_id, 10)
    top_artists = get_top_played_artists(user_id, 10)
    usuals = get_usuals(user_id, 10)
    trending_artists = get_trending_artists_for_user(user_id, 10)

    taste["top_played_songs"] = top_songs
    taste["top_played_artists"] = top_artists
    taste["usuals"] = usuals
    taste["trending_artists"] = trending_artists
    taste["total_plays"] = sum(s.get("count", 0) for s in top_songs)

    return taste


def _get_base_taste(user_id: str) -> dict:
    try:
        favorites = db.get_user_favorites(user_id)
        history = db.get_recently_played(user_id, 50)

        artist_counter = Counter()
        genre_counter = Counter()
        lang_counter = Counter()
        mood_counter = Counter()
        tempo_counter = Counter()

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

            mood = item.get("mood", "")
            if mood:
                mood_counter[mood] += 1

            tempo = item.get("tempo", "")
            if tempo:
                tempo_counter[tempo] += 1

        # NOW FIXED: Get preferred mood and tempo from taste profile
        taste_profile = db._load("taste_profiles").get(user_id, {})
        preferred_mood = None
        preferred_tempo = None

        if taste_profile.get("moods"):
            preferred_mood = max(taste_profile["moods"], key=taste_profile["moods"].get)
        if taste_profile.get("tempos"):
            preferred_tempo = max(taste_profile["tempos"], key=taste_profile["tempos"].get)

        return {
            "top_artists": artist_counter.most_common(10),
            "top_genres": genre_counter.most_common(5),
            "top_languages": lang_counter.most_common(5),
            "top_moods": mood_counter.most_common(5),
            "top_tempos": tempo_counter.most_common(5),
            "preferred_mood": preferred_mood,
            "preferred_tempo": preferred_tempo,
            "total_plays": len(history),
            "liked_songs": [f.get("song_id") for f in favorites],
            "disliked_songs": [],
        }
    except Exception as e:
        print(f"[TASTE ERROR] {e}")
        return {
            "top_artists": [],
            "top_genres": [],
            "top_languages": [],
            "top_moods": [],
            "top_tempos": [],
            "preferred_mood": None,
            "preferred_tempo": None,
            "total_plays": 0,
            "liked_songs": [],
            "disliked_songs": [],
        }


def on_song_skipped(user_id: str, song_data: dict, listen_seconds: int = 3):
    if not user_id:
        return

    song_id = song_data.get("song_id") or song_data.get("id") or song_data.get("songId") or ""
    if not song_id:
        return

    skips = db._load("song_skips")
    if user_id not in skips:
        skips[user_id] = {}

    if song_id not in skips[user_id]:
        skips[user_id][song_id] = {
            "count": 0,
            "title": song_data.get("title", "Unknown"),
            "artist": song_data.get("artist", "Unknown"),
        }

    skips[user_id][song_id]["count"] += 1
    skips[user_id][song_id]["last_listen_seconds"] = listen_seconds
    db._save("song_skips", skips)

    print(f"[TRACKER] Skipped '{song_data.get('title', song_id)}' after {listen_seconds}s "
          f"(total skips: {skips[user_id][song_id]['count']})")


def on_song_played(user_id: str, song_data: dict, listen_seconds: int = 60):
    if not user_id:
        return
    if listen_seconds < 15:
        return
    record_play(user_id, song_data)


# NOW FIXED: on_song_liked actually updates taste profile
def on_song_liked(user_id: str, song_data: dict):
    """Update taste when user likes a song."""
    _update_taste_profile(user_id, song_data)


def get_liked_songs(user_id: str):
    try:
        favorites = db.get_user_favorites(user_id)
        return [f.get("song_id") for f in favorites]
    except:
        return []


def get_disliked_songs(user_id: str):
    return []


# NOW FIXED: Reads from actual taste profile instead of hardcoded "happy"
def get_preferred_mood(user_id: str):
    """Get user's preferred mood from taste profile."""
    taste = db._load("taste_profiles").get(user_id, {})
    if taste.get("moods"):
        return max(taste["moods"], key=taste["moods"].get)
    return "happy"
