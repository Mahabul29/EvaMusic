
# ═══════════════════════════════════════════════════════════════
# ADD THESE TO YOUR app.py (replace existing functions/routes)
# ═══════════════════════════════════════════════════════════════

# REPLACE the existing fetch_trending function with this:
def fetch_trending(limit=20, lang=None):
    """Try API first, fallback to local DB only if API fails."""
    # Try JioSaavn API trending first
    try:
        data = _call(get_trending_url(limit))
        if data and isinstance(data, list) and len(data) > 0:
            print(f"[fetch_trending] API returned {len(data)} songs")
            return data
        if data and isinstance(data, dict):
            for key in ["data", "results", "songs"]:
                inner = data.get(key)
                if isinstance(inner, list) and inner:
                    print(f"[fetch_trending] API returned {len(inner)} songs")
                    return inner
    except Exception as e:
        print(f"[fetch_trending] API failed: {e}")

    # Fallback: local database
    print("[fetch_trending] Falling back to local DB")
    if lang and lang.lower() != 'all':
        return get_local_songs(lang, limit)
    all_songs = []
    for db_entry in LANG_DB.values():
        all_songs.extend(db_entry['songs'])
    random.shuffle(all_songs)
    return all_songs[:limit]


# ADD this new API route (put with other API routes):
@app.route('/api/similar-songs/<song_id>')
def api_similar_songs(song_id):
    """Get songs similar to the given song ID."""
    from suggest import get_similar_songs

    # Get the current song details
    current_song = fetch_song(song_id)
    if not current_song:
        return jsonify([])

    # Get candidate songs from trending/search
    lang = request.args.get('lang', 'All')
    candidates = fetch_trending(60, lang)

    # If not enough candidates, search by artist name
    if len(candidates) < 10 and current_song.get('artist'):
        artist_songs = fetch_songs(current_song['artist'], 20)
        candidates.extend(artist_songs)

    similar = get_similar_songs(current_song, candidates, limit=10)
    return jsonify(similar)


# REPLACE existing api_artists route with this behavior-based one:
@app.route('/api/artists')
def api_artists():
    """Get artists based on user taste behavior."""
    from user.trackuser import get_full_taste_summary, get_top_played_artists

    user_id = get_user_id()
    limit = request.args.get('limit', 10, type=int)
    lang = request.args.get('lang', 'All')

    print(f"[API] /api/artists called for user={user_id[:8]}... lang={lang}")

    # Try taste-based artists first (from user's play history)
    taste = get_full_taste_summary(user_id)
    top_artists = get_top_played_artists(user_id, limit)

    if top_artists:
        # User has listening history - return their top artists
        result = []
        for a in top_artists:
            result.append({
                "name": a.get("name") or a.get("artist", "Unknown"),
                "image": a.get("image_url") or a.get("image", "/static/images/default-album.png"),
                "genre": "Trending For You",
                "play_count": a.get("count", 0),
            })
        print(f"[API] Returning {len(result)} taste-based artists")
        return jsonify(result)

    # New user - return local DB artists
    print("[API] No taste history, returning local artists")
    if lang and lang.lower() != 'all':
        artists = get_local_artists(lang, limit)
    else:
        all_artists = []
        for db_entry in LANG_DB.values():
            all_artists.extend(db_entry['artists'])
        random.shuffle(all_artists)
        artists = all_artists[:limit]

    return jsonify(artists)
