"""
EvaMusic — Profile & Settings Routes
Fixed: removed broken 'models' import, fixed syntax errors, added /settings route.
"""

from flask import Blueprint, render_template, request, jsonify, session
import database as db
import uuid

profile_bp = Blueprint('profile', __name__)

def get_user_id():
    if 'user_id' in session:
        return session['user_id']
    if 'guest_id' not in session:
        session['guest_id'] = str(uuid.uuid4())[:8]
    return session['guest_id']

# ── PROFILE ────────────────────────────────────────────────────

@profile_bp.route('/profile')
def profile():
    user_id = get_user_id()
    favorites = db.get_user_favorites(user_id) or []
    recently_played = db.get_recently_played(user_id) or []

    # Normalize favorites keys for the template
    normalized_favs = []
    for f in favorites:
        normalized_favs.append({
            "song_id":   f.get("id", ""),
            "title":     f.get("title", "Unknown"),
            "artist":    f.get("artist", "Unknown"),
            "image_url": f.get("image", "/static/images/default-album.png"),
            "audio_url": f.get("url", ""),
        })

    # Load user data from database if logged in
    users = db._load("users")
    user_data = users.get(user_id, {})

    if user_data:
        profile_data = {
            "username":     user_data.get("username", user_id),
            "display_name": user_data.get("display_name", user_data.get("name", "Music Lover")),
            "bio":          user_data.get("bio", "Music lover"),
            "picture":      user_data.get("picture", ""),
            "social_links": user_data.get("social_links", {}),
        }
    else:
        profile_data = {
            "username":     user_id,
            "display_name": session.get('username', 'Music Lover'),
            "bio":          "",
            "picture":      "",
            "social_links": {},
        }

    stats = {
        "total_favorites":  len(favorites),
        "total_playlists":  0,
        "total_plays":      len(recently_played),
        "listening_hours":  0,
    }

    return render_template('profile.html',
        profile=profile_data,
        stats=stats,
        recently_played=recently_played,
        favorites=normalized_favs,
        playlists=[],
        title="Profile"
    )

# ── SETTINGS ───────────────────────────────────────────────────

@profile_bp.route('/settings')
def settings():
    return render_template('settings.html', title="Settings")

# ── FAVORITES PAGE ─────────────────────────────────────────────

@profile_bp.route('/favorites')
def profile_favorites():
    user_id = get_user_id()
    favorites = db.get_user_favorites(user_id)
    return render_template('favorites.html',
        songs=favorites,
        title="My Favorites",
        section="favorites"
    )

# ── HISTORY PAGE ───────────────────────────────────────────────

@profile_bp.route('/history')
def profile_history():
    user_id = get_user_id()
    history = db.get_recently_played(user_id, limit=100)
    return render_template('history.html',
        songs=history,
        title="Listening History",
        section="history"
    )

# ── PROFILE API ────────────────────────────────────────────────

@profile_bp.route('/api/profile/update', methods=['POST'])
def api_update_profile():
    user_id = get_user_id()
    data = request.get_json(silent=True) or {}
    if "username" in data:
        session['username'] = data["username"]
    return jsonify({"success": True})

@profile_bp.route('/api/profile/me', methods=['DELETE'])
def api_delete_profile():
    session.clear()
    return jsonify({"success": True})
        
