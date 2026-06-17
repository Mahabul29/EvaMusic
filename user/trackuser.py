"""
user/trackuser.py  —  User Profile and Taste Modeling Engine

Tracks explicit likes and listening habits to build an operational profile
of favorite languages, artists, moods, and genres.
"""

from collections import Counter
import database as db

# ═══════════════════════════════════════════════════════════════
# TRACKING RULES & DICTIONARIES
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
    'diljit dosanjh': 'punjabi', 'sidhu moose wala': 'punjabi',
    'karan aujla': 'punjabi', 'ap dhillon': 'punjabi', 'shubh': 'punjabi',
    'taylor swift': 'english', 'ed sheeran': 'english', 'drake': 'english',
    'the weeknd': 'english', 'ariana grande': 'english', 'justin bieber': 'english',
    'anirudh ravichander': 'tamil', 'yuvan shankar raja': 'tamil',
    's. thaman': 'telugu', 'devi sri prasad': 'telugu',
    'anupam roy': 'bengali', 'jeet gannguli': 'bengali',
    'ajay-atul': 'marathi', 'nusrat fateh ali khan': 'urdu'
}

def _detect_song_language(song):
    """Identifies the operational language profile of a song metadata block."""
    artist = (song.get('artist') or '').lower()
    for artist_name, lang in ARTIST_LANG_MAP.items():
        if artist_name in artist or artist in artist_name:
            return lang

    title = (song.get('title') or song.get('name') or '').lower()
    for lang, indicators in LANG_INDICATORS.items():
        for indicator in indicators:
            if indicator in title or indicator in artist:
                return lang

    lang_field = (song.get('language') or '').lower()
    if lang_field and lang_field in LANG_INDICATORS:
        return lang_field

    return 'hindi'

# ═══════════════════════════════════════════════════════════════
# INTERACTION PROCESSING
# ═══════════════════════════════════════════════════════════════

def on_song_liked(user_id, song_data):
    """
    Hook execution triggered when a user favorites a song.
    Can be expanded for real-time calculation drops or analytics hooks.
    """
    song_id = song_data.get('id')
    title = song_data.get('title')
    print(f"[TASTE ENGINE] Track processing liked song: {title} ({song_id}) for user {user_id}")


def get_full_taste_summary(user_id):
    """
    Queries history log buffers and explicit favorite tables to return
    a sorted summary matrix of user music preferences.
    """
    favorites = db.get_user_favorites(user_id)
    history = db.get_recently_played(user_id, limit=50)

    artist_counter = Counter()
    lang_counter = Counter()
    genre_counter = Counter()
    mood_counter = Counter()

    # 1. Process explicit highly-weighted favorites matrix items
    for f in favorites:
        # Extract artists safely
        artists_str = f.get('artist') or 'Unknown'
        for a in artists_str.split(','):
            name = a.strip().title()
            if name and name != 'Unknown':
                artist_counter[name] += 5  # Favorites carry higher score weights

        # Check explicit tags or back-evaluate fallback values
        lang = _detect_song_language(f)
        lang_counter[lang] += 5

        genre = f.get('genre') or f.get('album') or ''
        if genre and len(genre) > 2:
            genre_counter[genre.title()] += 3

    # 2. Process implicit streaming playback events (lower scalar weight)
    for h in history:
        artists_str = h.get('artist') or 'Unknown'
        for a in artists_str.split(','):
            name = a.strip().title()
            if name and name != 'Unknown':
                artist_counter[name] += 1

        lang = _detect_song_language({
            'title': h.get('title'),
            'artist': h.get('artist')
        })
        lang_counter[lang] += 1

        genre = h.get('genre') or h.get('album') or ''
        if genre and len(genre) > 2:
            genre_counter[genre.title()] += 1

    # 3. Handle default empty states beautifully
    if not artist_counter and not lang_counter:
        return {
            'top_artists': [],
            'top_languages': [('Hindi', 1)],
            'top_genres': [],
            'top_moods': [('Happy', 1)],
            'metrics_collected': 0
        }

    # Sort down collected vectors 
    sorted_artists = artist_counter.most_common(10)
    sorted_langs = [(l.title(), w) for l, w in lang_counter.most_common(5)]
    sorted_genres = genre_counter.most_common(5)

    # Simple dynamic mood deduction from computed genre strings
    for g, weight in sorted_genres:
        g_lower = g.lower()
        if 'romantic' in g_lower or 'love' in g_lower:
            mood_counter['Romantic'] += weight
        elif 'sad' in g_lower or 'broken' in g_lower or 'pain' in g_lower:
            mood_counter['Melancholic'] += weight
        elif 'dance' in g_lower or 'party' in g_lower or 'hip hop' in g_lower:
            mood_counter['Energetic'] += weight
        else:
            mood_counter['Chill'] += 1

    if not mood_counter:
        mood_counter['Chill'] = 1

    return {
        'top_artists': sorted_artists,
        'top_languages': sorted_langs,
        'top_genres': sorted_genres,
        'top_moods': mood_counter.most_common(3),
        'metrics_collected': len(favorites) + len(history)
        }
    
