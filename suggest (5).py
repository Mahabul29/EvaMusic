"""
suggest.py  —  EvaMusic smart recommendation engine

What changed:
- Added get_similar_songs() — finds songs by same artist/language/genre
- Added get_similar_artists() — finds related artists
- get_because_you_liked() now shows even if no liked songs (uses play history)
- Better scoring for new users
- No circular imports — all app imports are done inside functions
"""

import random
from collections import Counter


def get_similar_songs(song, limit=10):
    """Find songs similar to the given song by artist, language, or genre."""
    # Import here to avoid circular imports at module level
    from app import fetch_songs, _normalize_song, _filter_by_language, _detect_song_language, LANG_INDICATORS

    artist = (song.get('artist') or song.get('primaryArtists') or '').lower()
    title = (song.get('title') or song.get('name') or '').lower()
    lang = _detect_song_language(song)

    results = []
    seen_ids = {str(song.get('id', ''))}

    # 1. Search by artist name
    if artist and artist != 'unknown':
        try:
            raw = fetch_songs(artist.split(',')[0].strip(), limit * 2)
            for s in raw:
                norm = _normalize_song(s)
                if norm and str(norm.get('id', '')) not in seen_ids:
                    seen_ids.add(str(norm.get('id', '')))
                    results.append(norm)
        except Exception as e:
            print(f"[get_similar_songs] Artist search error: {e}")

    # 2. If not enough, search by language indicators
    if len(results) < limit:
        for indicator in LANG_INDICATORS.get(lang, []):
            try:
                raw = fetch_songs(indicator, limit)
                for s in raw:
                    norm = _normalize_song(s)
                    if norm and str(norm.get('id', '')) not in seen_ids:
                        seen_ids.add(str(norm.get('id', '')))
                        results.append(norm)
                if len(results) >= limit * 2:
                    break
            except Exception as e:
                print(f"[get_similar_songs] Language search error: {e}")

    # 3. Score by similarity
    def score(s):
        s_artist = (s.get('artist') or '').lower()
        s_artist_match = 0
        if artist and artist != 'unknown':
            for a in artist.split(','):
                a = a.strip()
                if a and a in s_artist:
                    s_artist_match = 3
                    break
        s_lang = _detect_song_language(s)
        s_lang_match = 2 if s_lang == lang else 0
        return s_artist_match + s_lang_match

    results.sort(key=score, reverse=True)
    return results[:limit]


def get_similar_artists(artist_name, limit=5):
    """Find artists similar to the given artist name."""
    from app import ARTIST_LANG_MAP

    artist_name = artist_name.lower().strip()

    # Detect language of the artist
    detected_lang = None
    for a_name, a_lang in ARTIST_LANG_MAP.items():
        if a_name in artist_name or artist_name in a_name:
            detected_lang = a_lang
            break

    if not detected_lang:
        detected_lang = 'hindi'

    # Find artists of same language from the map
    similar = []
    seen = {artist_name}

    for name, lang in ARTIST_LANG_MAP.items():
        if lang == detected_lang and name not in seen:
            seen.add(name)
            similar.append({
                'id': name.replace(' ', '_'),
                'name': name.title(),
                'image': '/static/images/default-album.png',
                'language': lang,
                'genre': 'Similar Artist',
                'source': 'similar'
            })
        if len(similar) >= limit:
            break

    return similar


def get_because_you_liked(user_id, trending_pool, limit=10):
    """
    Show songs similar to what the user liked or played.
    Works even for new users (uses play history as fallback).
    """
    import database as db
    from user.trackuser import get_full_taste_summary

    taste = get_full_taste_summary(user_id)
    liked_songs = db.get_user_favorites(user_id)

    # If no liked songs, use recently played as fallback
    if not liked_songs:
        history = db.get_recently_played(user_id, 5)
        if history:
            liked_songs = history

    if not liked_songs:
        # New user — return random trending
        return random.sample(trending_pool, min(limit, len(trending_pool))) if trending_pool else []

    # Pick a random liked/played song as seed
    seed = random.choice(liked_songs)

    # Find similar songs
    similar = get_similar_songs(seed, limit=limit * 2)

    # Also mix in trending songs that match taste
    top_artists = [a[0].lower() for a in taste.get('top_artists', [])[:3]]
    top_langs = [l[0].lower() for l in taste.get('top_languages', [])[:2]]

    from app import _detect_song_language
    scored_trending = []
    for song in trending_pool:
        s_artist = (song.get('artist') or '').lower()
        s_lang = _detect_song_language(song)

        score = 0
        for ta in top_artists:
            if ta in s_artist:
                score += 2
        for tl in top_langs:
            if s_lang == tl:
                score += 1

        if score > 0:
            scored_trending.append((score, song))

    scored_trending.sort(key=lambda x: x[0], reverse=True)

    # Combine: similar songs + trending matches
    combined = similar[:limit // 2]
    seen_ids = {str(s.get('id', '')) for s in combined}

    for _, song in scored_trending:
        sid = str(song.get('id', ''))
        if sid not in seen_ids:
            seen_ids.add(sid)
            combined.append(song)
        if len(combined) >= limit:
            break

    # Pad with random trending if still not enough
    if len(combined) < limit:
        for song in trending_pool:
            sid = str(song.get('id', ''))
            if sid not in seen_ids:
                seen_ids.add(sid)
                combined.append(song)
            if len(combined) >= limit:
                break

    return combined[:limit]


def get_suggestions_for_user(user_id, song_pool, limit=20):
    """
    Rank a pool of songs by how well they match the user's taste.
    """
    from user.trackuser import get_full_taste_summary
    from app import _detect_song_language

    taste = get_full_taste_summary(user_id)

    if not taste or not taste.get('top_artists'):
        # New user — return random selection
        if len(song_pool) <= limit:
            return song_pool
        return random.sample(song_pool, limit)

    top_artists = [a[0].lower() for a in taste.get('top_artists', [])]
    top_genres = [g[0].lower() for g in taste.get('top_genres', [])]
    top_languages = [l[0].lower() for l in taste.get('top_languages', [])]
    top_moods = [m[0].lower() for m in taste.get('top_moods', [])]

    scored = []
    for song in song_pool:
        score = 0

        # Artist match
        s_artist = (song.get('artist') or song.get('primaryArtists') or '').lower()
        for i, ta in enumerate(top_artists):
            if ta in s_artist:
                score += max(5 - i, 1)  # Higher score for top artists

        # Language match
        s_lang = _detect_song_language(song)
        for i, tl in enumerate(top_languages):
            if s_lang == tl:
                score += max(3 - i, 1)

        # Genre match
        s_genre = (song.get('genre') or '').lower()
        for tg in top_genres:
            if tg in s_genre:
                score += 2

        # Mood match
        s_mood = (song.get('mood') or '').lower()
        for tm in top_moods:
            if tm in s_mood:
                score += 1

        # Small random factor to avoid same order every time
        score += random.uniform(0, 0.5)

        scored.append((score, song))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:limit]]


def build_homepage_sections(user_id, trending_pool):
    """
    Build all smart homepage sections.
    Returns dict with keys: for_you, because_you_liked, your_artists, trending, etc.
    """
    import database as db
    from user.trackuser import get_full_taste_summary

    taste = get_full_taste_summary(user_id)
    sections = {}

    # 1. For You — personalized trending
    sections['for_you'] = get_suggestions_for_user(user_id, trending_pool, limit=20)

    # 2. Because You Liked — similar to liked/played songs
    sections['because_you_liked'] = get_because_you_liked(user_id, trending_pool, limit=10)

    # 3. Your Artists — top artists from taste
    top_artists = taste.get('top_artists', [])[:10]
    artist_cards = []
    for name, weight in top_artists:
        artist_cards.append({
            'id': name.lower().replace(' ', '_'),
            'name': name,
            'image': '/static/images/default-album.png',
            'language': 'hindi',
            'genre': 'Your Top',
            'source': 'taste'
        })
    sections['your_artists'] = artist_cards

    # 4. Trending Now
    sections['trending'] = trending_pool[:10]

    # 5. Your Usuals — most played songs
    history = db.get_recently_played(user_id, 50)
    if history:
        play_counts = Counter()
        for h in history:
            play_counts[h.get('song_id', '')] += 1

        usuals = []
        seen = set()
        for song_id, count in play_counts.most_common(10):
            if count >= 2:  # Played at least 2 times
                for h in history:
                    if h.get('song_id') == song_id and song_id not in seen:
                        seen.add(song_id)
                        usuals.append({
                            'id': song_id,
                            'title': h.get('title', 'Unknown'),
                            'artist': h.get('artist', 'Unknown'),
                            'image': h.get('image_url', '/static/images/default-album.png'),
                            'plays': count
                        })
                        break
        sections['your_usuals'] = usuals
    else:
        sections['your_usuals'] = []

    # 6. Recommended For You — for new users
    if not taste.get('top_artists'):
        sections['recommended'] = random.sample(trending_pool, min(10, len(trending_pool))) if trending_pool else []
    else:
        sections['recommended'] = sections['for_you'][:10]

    return sections
