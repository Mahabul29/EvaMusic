"""
suggest.py  —  EvaMusic smart recommendation engine

What changed:
- Added fetch_songs_func parameters to eliminate circular dependencies with app.py.
- Handled empty trending pool arrays defensively to avoid indexing or random sample failures.
"""

import random
import re
from collections import Counter

# ═══════════════════════════════════════════════════════════════
# LOCAL COPIES OF APP HELPERS (to avoid circular imports)
# ═══════════════════════════════════════════════════════════════

LANG_INDICATORS = {
    'hindi':     ['hindi', 'bollywood', 'हिंदी'],
    'english':   ['english', 'pop', 'rock', 'edm', 'hip-hop', 'r&b'],
    'punjabi':   ['punjabi', 'bhangra', 'ਪੰਜਾਬੀ'],
    'tamil':     ['tamil', 'kollywood', 'தமிழ்'],
    'telugu':    ['telugu', 'tollywood', 'తెలుగు'],
    'marathi':   ['marathi', 'मराठी'],
    'gujarati':  ['gujarati', 'ગુજરાતી'],
    'bengali':   ['bengali', 'bangla', 'বাংলা'],
    'kannada':   ['kannada', 'sandalwood', 'ಕನ್ನಡ'],
    'malayalam': ['malayalam', 'mollywood', 'മലയാളം'],
    'urdu':      ['urdu', 'اردو', 'ghazal', 'qawwali'],
}

ARTIST_LANG_MAP = {
    'arijit singh': 'hindi', 'shreya ghoshal': 'hindi', 'sonu nigam': 'hindi',
    'jubin nautiyal': 'hindi', 'neha kakkar': 'hindi', 'atif aslam': 'hindi',
    'armaan malik': 'hindi', 'vishal mishra': 'hindi', 'pritam': 'hindi',
    'a.r. rahman': 'hindi', 'shankar ehsaan loy': 'hindi', 'badshah': 'hindi',
    'guru randhawa': 'hindi', 'jass manak': 'hindi', 'darshan raval': 'hindi',
    'tony kakkar': 'hindi', 'javed ali': 'hindi', 'mohit chauhan': 'hindi',
    'kk': 'hindi', 'kumar sanu': 'hindi', 'udit narayan': 'hindi',
    'alka yagnik': 'hindi', 'sunidhi chauhan': 'hindi', 'shreya': 'hindi',
    'arijit': 'hindi', 'jubin': 'hindi', 'neha': 'hindi',
    'kishore kumar': 'hindi', 'lata mangeshkar': 'hindi', 'asha bhosle': 'hindi',
    'rahat fateh ali khan': 'hindi', 'ankur r pathakk': 'hindi',
    'raghav chaitanya': 'hindi', 'hansraj raghuwanshi': 'hindi',
    'vishal dadlani': 'hindi', 'shekhar ravjiani': 'hindi',
    'diljit dosanjh': 'punjabi', 'sidhu moose wala': 'punjabi',
    'karan aujla': 'punjabi', 'ap dhillon': 'punjabi', 'shubh': 'punjabi',
    'jasmine sandlas': 'punjabi', 'amrinder gill': 'punjabi',
    'babbu maan': 'punjabi', 'gippy grewal': 'punjabi',
    'jassie gill': 'punjabi', 'mankirt aulakh': 'punjabi',
    'nimrat khaira': 'punjabi', 'akhil': 'punjabi',
    'jind universe': 'punjabi', 'wavy': 'punjabi',
    'taylor swift': 'english', 'ed sheeran': 'english', 'drake': 'english',
    'the weeknd': 'english', 'ariana grande': 'english', 'justin bieber': 'english',
    'billie eilish': 'english', 'dua lipa': 'english', 'bruno mars': 'english',
    'coldplay': 'english', 'imagine dragons': 'english', 'maroon 5': 'english',
    'post malone': 'english', 'travis scott': 'english', 'eminem': 'english',
    'rihanna': 'english', 'beyoncé': 'english', 'sia': 'english',
    'anirudh ravichander': 'tamil', 'a.r. rahman': 'tamil', 'yuvan shankar raja': 'tamil',
    'g.v. prakash kumar': 'tamil', 'hiphop tamizha': 'tamil',
    'santhosh narayanan': 'tamil', 'd. imman': 'tamil',
    's. thaman': 'telugu', 'devi sri prasad': 'telugu',
    'anirudh': 'telugu', 'mickey j meyer': 'telugu',
    'arijit singh': 'bengali', 'anupam roy': 'bengali',
    'jeet gannguli': 'bengali', 'shreya ghoshal': 'bengali',
    'ajay-atul': 'marathi', 'avdhoot gupte': 'marathi',
    'nusrat fateh ali khan': 'urdu', 'rahat fateh ali khan': 'urdu',
    'atif aslam': 'urdu', 'ali zafar': 'urdu',
}


def _detect_song_language_local(song):
    """Local copy of language detection (no app import)."""
    artist = (song.get('artist') or song.get('primaryArtists') or song.get('singers') or '').lower()
    for artist_name, lang in ARTIST_LANG_MAP.items():
        if artist_name in artist or artist in artist_name:
            return lang

    title = (song.get('title') or song.get('name') or '').lower()
    for lang, indicators in LANG_INDICATORS.items():
        for indicator in indicators:
            if indicator in title or indicator in artist:
                return lang

    album = (song.get('album') or '').lower()
    for lang, indicators in LANG_INDICATORS.items():
        for indicator in indicators:
            if indicator in album:
                return lang

    lang_field = (song.get('language') or '').lower()
    if lang_field and lang_field in LANG_INDICATORS:
        return lang_field

    return 'hindi'


def _normalize_song_local(data):
    """Local copy of song normalization (no app import)."""
    if not data:
        return None

    inner = data
    for wrapper in ["data", "song", "result"]:
        candidate = data.get(wrapper)
        if isinstance(candidate, dict):
            inner = candidate
            break
        elif isinstance(candidate, list) and candidate:
            inner = candidate[0]
            break

    # Extract audio URL
    URL_KEYS = ["url", "downloadUrl", "download_url", "media_url",
                "audio_url", "stream_url", "song_url", "link"]
    audio_url = ""
    for key in URL_KEYS:
        val = inner.get(key)
        if val:
            if isinstance(val, list) and val:
                entry = val[-1]
                if isinstance(entry, dict):
                    audio_url = entry.get("url") or entry.get("link") or ""
                elif isinstance(entry, str):
                    audio_url = entry
            elif isinstance(val, str) and val.startswith("http"):
                audio_url = val
        if audio_url:
            break

    image = inner.get("image") or inner.get("image_url") or inner.get("thumbnail") or ""
    if isinstance(image, list) and image:
        entry = image[-1]
        image = entry.get("url") or entry.get("link") or (entry if isinstance(entry, str) else "") or ""

    return {
        "id":       inner.get("id") or inner.get("song_id") or data.get("id") or "",
        "title":    inner.get("title") or inner.get("name") or inner.get("song") or "Unknown",
        "artist":   inner.get("artist") or inner.get("primaryArtists") or inner.get("singers") or "Unknown",
        "album":    inner.get("album") or inner.get("album_name") or "",
        "duration": inner.get("duration") or inner.get("length") or 0,
        "image":    image or "/static/images/default-album.png",
        "url":      audio_url,
    }


# ═══════════════════════════════════════════════════════════════
# MAIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_similar_songs(song, fetch_songs_func, limit=10):
    """Find songs similar to the given song by artist, language, or genre."""
    artist = (song.get('artist') or song.get('primaryArtists') or '').lower()
    title = (song.get('title') or song.get('name') or '').lower()
    lang = _detect_song_language_local(song)

    results = []
    seen_ids = {str(song.get('id', ''))}

    # 1. Search by artist name
    if artist and artist != 'unknown':
        try:
            raw = fetch_songs_func(artist.split(',')[0].strip(), limit * 2)
            for s in raw:
                norm = _normalize_song_local(s)
                if norm and str(norm.get('id', '')) not in seen_ids:
                    seen_ids.add(str(norm.get('id', '')))
                    results.append(norm)
        except Exception as e:
            print(f"[get_similar_songs] Artist search error: {e}")

    # 2. If not enough, search by language indicators
    if len(results) < limit:
        for indicator in LANG_INDICATORS.get(lang, []):
            try:
                raw = fetch_songs_func(indicator, limit)
                for s in raw:
                    norm = _normalize_song_local(s)
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
        s_lang = _detect_song_language_local(s)
        s_lang_match = 2 if s_lang == lang else 0
        return s_artist_match + s_lang_match

    results.sort(key=score, reverse=True)
    return results[:limit]


def get_similar_artists(artist_name, limit=5):
    """Find artists similar to the given artist name."""
    artist_name = artist_name.lower().strip()

    detected_lang = None
    for a_name, a_lang in ARTIST_LANG_MAP.items():
        if a_name in artist_name or artist_name in a_name:
            detected_lang = a_lang
            break

    if not detected_lang:
        detected_lang = 'hindi'

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


def get_because_you_liked(user_id, trending_pool, fetch_songs_func, limit=10):
    """Show songs similar to what the user liked or played."""
    import database as db
    from user.trackuser import get_full_taste_summary

    taste = get_full_taste_summary(user_id)
    liked_songs = db.get_user_favorites(user_id)

    if not liked_songs:
        history = db.get_recently_played(user_id, 5)
        if history:
            liked_songs = history

    if not liked_songs:
        return random.sample(trending_pool, min(limit, len(trending_pool))) if trending_pool else []

    seed = random.choice(liked_songs)
    similar = get_similar_songs(seed, fetch_songs_func, limit=limit * 2)

    top_artists = [a[0].lower() for a in taste.get('top_artists', [])[:3]]
    top_langs = [l[0].lower() for l in taste.get('top_languages', [])[:2]]

    scored_trending = []
    for song in trending_pool:
        s_artist = (song.get('artist') or '').lower()
        s_lang = _detect_song_language_local(song)

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

    combined = similar[:limit // 2]
    seen_ids = {str(s.get('id', '')) for s in combined}

    for _, song in scored_trending:
        sid = str(song.get('id', ''))
        if sid not in seen_ids:
            seen_ids.add(sid)
            combined.append(song)
        if len(combined) >= limit:
            break

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
    """Rank a pool of songs by how well they match the user's taste."""
    from user.trackuser import get_full_taste_summary

    taste = get_full_taste_summary(user_id)

    if not taste or not taste.get('top_artists'):
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

        s_artist = (song.get('artist') or song.get('primaryArtists') or '').lower()
        for i, ta in enumerate(top_artists):
            if ta in s_artist:
                score += max(5 - i, 1)

        s_lang = _detect_song_language_local(song)
        for i, tl in enumerate(top_languages):
            if s_lang == tl:
                score += max(3 - i, 1)

        s_genre = (song.get('genre') or '').lower()
        for tg in top_genres:
            if tg in s_genre:
                score += 2

        s_mood = (song.get('mood') or '').lower()
        for tm in top_moods:
            if tm in s_mood:
                score += 1

        score += random.uniform(0, 0.5)
        scored.append((score, song))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:limit]]


def build_homepage_sections(user_id, trending_pool, fetch_songs_func):
    """Build all smart homepage sections safely."""
    import database as db
    from user.trackuser import get_full_taste_summary

    taste = get_full_taste_summary(user_id)
    sections = {}

    # 1. For You
    sections['for_you'] = get_suggestions_for_user(user_id, trending_pool, limit=20)

    # 2. Because You Liked
    sections['because_you_liked'] = get_because_you_liked(user_id, trending_pool, fetch_songs_func, limit=10)

    # 3. Your Artists
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

    # 4. Trending Now (safely bounded)
    sections['trending'] = trending_pool[:10] if trending_pool else []

    # 5. Your Usuals
    history = db.get_recently_played(user_id, 50)
    if history:
        play_counts = Counter()
        for h in history:
            play_counts[h.get('song_id', '')] += 1

        usuals = []
        seen = set()
        for song_id, count in play_counts.most_common(10):
            if count >= 2:
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

    # 6. Recommended For You
    if not taste.get('top_artists'):
        sections['recommended'] = random.sample(trending_pool, min(10, len(trending_pool))) if trending_pool else []
    else:
        sections['recommended'] = sections['for_you'][:10] if sections.get('for_you') else []

    return sections
