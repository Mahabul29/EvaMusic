# ═══════════════════════════════════════════════════════════════
# MINIMAL FIX - Replace these 3 functions in your app.py
# ═══════════════════════════════════════════════════════════════

# 1. REPLACE fetch_trending (add lang parameter):
def fetch_trending(limit=20, lang=None):
    global _LAST_GOOD_TRENDING, _LAST_GOOD_TRENDING_LANG

    cache_key = lang.lower() if lang else 'all'
    if cache_key in _LAST_GOOD_TRENDING_LANG:
        cached = _LAST_GOOD_TRENDING_LANG[cache_key]
        if cached:
            return cached[:limit]

    data = _call(get_trending_url(limit * 5))
    songs = []
    if isinstance(data, list) and data:
        songs = data
    if isinstance(data, dict):
        for key in ["data", "results", "songs"]:
            inner = data.get(key)
            if isinstance(inner, list) and inner:
                songs = inner
                break

    if songs:
        _LAST_GOOD_TRENDING = songs
        if lang and lang.lower() != 'all':
            songs = _filter_by_language(songs, lang)
        _LAST_GOOD_TRENDING_LANG[cache_key] = songs
        return songs[:limit]

    if _LAST_GOOD_TRENDING:
        filtered = _filter_by_language(_LAST_GOOD_TRENDING, lang)
        return filtered[:limit]
    return []


# 2. REPLACE api_trending (add lang parameter):
@app.route('/api/trending')
def api_trending():
    limit = request.args.get('limit', 20, type=int)
    lang = request.args.get('lang', 'All')
    songs = fetch_trending(limit, lang)
    return jsonify(songs)


# 3. REPLACE api_artists (add lang filter):
@app.route('/api/artists')
def api_artists():
    user_id = get_user_id()
    lang = request.args.get('lang', 'All')
    limit = request.args.get('limit', 10, type=int)

    taste = get_full_taste_summary(user_id)
    artists = []
    seen = set()

    # From top artists
    for artist_name, weight in taste.get('top_artists', [])[:limit*2]:
        key = artist_name.lower()
        if key in seen: continue
        seen.add(key)

        detected = None
        for a_name, a_lang in ARTIST_LANG_MAP.items():
            if a_name in key or key in a_name:
                detected = a_lang
                break

        if lang and lang.lower() != 'all':
            if detected and detected != lang.lower():
                continue

        artists.append({
            'id': key.replace(' ', '_'),
            'name': artist_name,
            'image': '/static/images/default-album.png',
            'language': detected or 'hindi',
            'genre': 'Your Top'
        })

    # From favorites
    try:
        favs = db.get_user_favorites(user_id)
        for item in favs:
            raw = item.get('artist', '')
            names = [a.strip() for a in re.split(r'[,/&]', raw) if a.strip()]
            for name in names:
                key = name.lower()
                if key in seen: continue
                seen.add(key)

                detected = None
                for a_name, a_lang in ARTIST_LANG_MAP.items():
                    if a_name in key or key in a_name:
                        detected = a_lang
                        break

                if lang and lang.lower() != 'all':
                    if detected and detected != lang.lower():
                        continue

                artists.append({
                    'id': key.replace(' ', '_'),
                    'name': name,
                    'image': item.get('image_url', '/static/images/default-album.png'),
                    'language': detected or 'hindi',
                    'genre': 'From Favorites'
                })
    except: pass

    # From history
    try:
        history = db.get_recently_played(user_id, 30)
        for item in history:
            raw = item.get('artist', '')
            names = [a.strip() for a in re.split(r'[,/&]', raw) if a.strip()]
            for name in names:
                key = name.lower()
                if key in seen: continue
                seen.add(key)

                detected = None
                for a_name, a_lang in ARTIST_LANG_MAP.items():
                    if a_name in key or key in a_name:
                        detected = a_lang
                        break

                if lang and lang.lower() != 'all':
                    if detected and detected != lang.lower():
                        continue

                artists.append({
                    'id': key.replace(' ', '_'),
                    'name': name,
                    'image': item.get('image_url', '/static/images/default-album.png'),
                    'language': detected or 'hindi',
                    'genre': 'Recently Played'
                })
    except: pass

    # Fallback to trending
    if len(artists) < limit:
        trending_songs = fetch_trending(limit * 3, lang)
        trending_artists = _extract_artists_from_songs(trending_songs, lang)
        for a in trending_artists:
            if a['id'] not in seen:
                seen.add(a['id'])
                artists.append(a)
            if len(artists) >= limit:
                break

    return jsonify(artists[:limit])
