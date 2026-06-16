# ═══════════════════════════════════════════════════════════════
# ADD/REPLACE IN YOUR app.py - Complete Working Routes
# ═══════════════════════════════════════════════════════════════

# 1. REPLACE existing fetch_trending() function:
def fetch_trending(limit=20, lang=None):
    """Try JioSaavn API first, fallback to local DB only if API fails."""
    # Try API trending first
    try:
        data = _call(get_trending_url(limit))
        if data and isinstance(data, list) and len(data) > 0:
            print(f"[fetch_trending] API: {len(data)} songs")
            return data
        if data and isinstance(data, dict):
            for key in ["data", "results", "songs"]:
                inner = data.get(key)
                if isinstance(inner, list) and inner:
                    print(f"[fetch_trending] API: {len(inner)} songs")
                    return inner
    except Exception as e:
        print(f"[fetch_trending] API error: {e}")

    # Fallback to local DB
    print("[fetch_trending] Fallback to local DB")
    if lang and lang.lower() != 'all':
        return get_local_songs(lang, limit)
    all_songs = []
    for db_entry in LANG_DB.values():
        all_songs.extend(db_entry['songs'])
    random.shuffle(all_songs)
    return all_songs[:limit]


# 2. REPLACE existing api_artists route:
@app.route('/api/artists')
def api_artists():
    """Get artists based on user taste (behavior), not random."""
    from user.trackuser import get_full_taste_summary, get_top_played_artists

    user_id = get_user_id()
    limit = request.args.get('limit', 10, type=int)
    lang = request.args.get('lang', 'All')

    print(f"[API] /api/artists user={user_id[:8]} lang={lang}")

    # Check if user has play history
    top_artists = get_top_played_artists(user_id, limit)

    if top_artists:
        # RETURN user's most-played artists
        result = []
        for a in top_artists:
            result.append({
                "name": a.get("name") or a.get("artist", "Unknown"),
                "image": a.get("image_url") or a.get("image", "/static/images/default-album.png"),
                "genre": "Your Top Artist",
                "play_count": a.get("count", 0),
            })
        print(f"[API] Returning {len(result)} behavior-based artists")
        return jsonify(result)

    # NEW USER: return local DB artists (random)
    print("[API] New user - returning local artists")
    if lang and lang.lower() != 'all':
        artists = get_local_artists(lang, limit)
    else:
        all_artists = []
        for db_entry in LANG_DB.values():
            all_artists.extend(db_entry['artists'])
        random.shuffle(all_artists)
        artists = all_artists[:limit]

    return jsonify(artists)


# 3. ADD this new route (put with other API routes):
@app.route('/api/similar-songs/<song_id>')
def api_similar_songs(song_id):
    """Get songs similar to the currently playing song."""
    from suggest import get_similar_songs

    # Get current song details
    current_song = fetch_song(song_id)
    if not current_song:
        return jsonify([])

    # Get candidates from trending + search by artist
    lang = request.args.get('lang', 'All')
    candidates = fetch_trending(60, lang)

    # Also search by artist name for more matches
    if current_song.get('artist'):
        artist_songs = fetch_songs(current_song['artist'], 20)
        candidates.extend(artist_songs)

    similar = get_similar_songs(current_song, candidates, limit=10)
    return jsonify(similar)


# 4. REPLACE existing api_trending_artists route:
@app.route('/api/trending-artists')
def api_trending_artists():
    """Return user's top played artists (Trending Artists)."""
    from user.trackuser import get_full_taste_summary
    user_id = get_user_id()
    limit = request.args.get('limit', 10, type=int)
    taste = get_full_taste_summary(user_id)
    artists = taste.get("top_played_artists") or []

    # Filter to artists with 2+ plays (lowered from 5)
    artists = [a for a in artists if a.get("count", 0) >= 2]

    result = [
        {
            "name": a.get("name") or a.get("artist") or "Unknown",
            "image": a.get("image_url") or a.get("image") or "/static/images/default-album.png",
            "genre": "Trending",
            "play_count": a.get("count", 0),
        }
        for a in artists
    ]
    return jsonify(result[:limit])
