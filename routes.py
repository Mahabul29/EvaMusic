"""
EvaMusic — Profile Routes
Handles all profile-related Flask routes and API endpoints.
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models import (
    get_profile, update_profile, create_profile, 
    get_profile_stats, delete_profile,
    AVATAR_OPTIONS, THEME_OPTIONS, ACCENT_COLORS
)
from database import (
    get_user_favorites, get_recently_played, 
    get_user_playlists, save_search
)
import uuid

# Create Blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


def get_user_id():
    """Get or create session user ID."""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
        session['username'] = f"user_{session['user_id']}"
    return session['user_id']


def ensure_profile():
    """Ensure user has a profile document in DB."""
    user_id = get_user_id()
    profile = get_profile(user_id)
    if not profile:
        username = session.get('username', f"user_{user_id}")
        create_profile(user_id, username)
    return user_id


# ═══════════════════════════════════════════════════════════════
# PROFILE PAGE ROUTES
# ═══════════════════════════════════════════════════════════════

@profile_bp.route('/')
def profile():
    """Main profile page."""
    user_id = ensure_profile()
    profile_data = get_profile(user_id)
    stats = get_profile_stats(user_id)

    if not profile_data:
        return redirect(url_for('profile.edit'))

    # Get recent activity
    favorites = get_user_favorites(user_id, limit=6)
    recently_played = get_recently_played(user_id, limit=10)
    playlists = get_user_playlists(user_id)

    return render_template('profile.html',
        profile=profile_data.to_dict(),
        stats=stats,
        favorites=favorites,
        recently_played=recently_played,
        playlists=playlists,
        title="My Profile"
    )


@profile_bp.route('/edit')
def edit_profile():
    """Edit profile page."""
    user_id = ensure_profile()
    profile_data = get_profile(user_id)

    return render_template('edit_profile.html',
        profile=profile_data.to_dict() if profile_data else {},
        avatars=AVATAR_OPTIONS,
        themes=THEME_OPTIONS,
        accent_colors=ACCENT_COLORS,
        title="Edit Profile"
    )


# ═══════════════════════════════════════════════════════════════
# PROFILE API ROUTES
# ═══════════════════════════════════════════════════════════════

@profile_bp.route('/api/me', methods=['GET'])
def api_get_profile():
    """Get current user's profile."""
    user_id = get_user_id()
    profile = get_profile(user_id)
    if profile:
        return jsonify({"success": True, "profile": profile.to_dict()})
    return jsonify({"success": False, "message": "Profile not found"}), 404


@profile_bp.route('/api/me', methods=['PUT', 'POST'])
def api_update_profile():
    """Update current user's profile."""
    user_id = ensure_profile()
    data = request.get_json() or request.form.to_dict()

    result = update_profile(user_id, data)
    return jsonify(result)


@profile_bp.route('/api/me/stats', methods=['GET'])
def api_get_stats():
    """Get user's listening statistics."""
    user_id = get_user_id()
    stats = get_profile_stats(user_id)
    return jsonify({"success": True, "stats": stats})


@profile_bp.route('/api/me/avatar', methods=['POST'])
def api_update_avatar():
    """Update user's avatar."""
    user_id = ensure_profile()
    data = request.get_json() or {}
    avatar_url = data.get("avatar_url")

    if avatar_url and avatar_url in AVATAR_OPTIONS:
        result = update_profile(user_id, {"avatar_url": avatar_url})
        return jsonify(result)
    return jsonify({"success": False, "message": "Invalid avatar"}), 400


@profile_bp.route('/api/me/theme', methods=['POST'])
def api_update_theme():
    """Update user's theme preference."""
    user_id = ensure_profile()
    data = request.get_json() or {}
    theme = data.get("theme")
    accent = data.get("accent_color")

    updates = {}
    profile = get_profile(user_id)
    prefs = profile.preferences if profile else {}

    if theme and theme in THEME_OPTIONS:
        prefs["theme"] = theme
    if accent and accent in ACCENT_COLORS:
        prefs["accent_color"] = accent

    updates["preferences"] = prefs
    result = update_profile(user_id, updates)
    return jsonify(result)


@profile_bp.route('/api/me/social', methods=['POST'])
def api_update_social():
    """Update social media links."""
    user_id = ensure_profile()
    data = request.get_json() or {}

    profile = get_profile(user_id)
    if not profile:
        return jsonify({"success": False, "message": "Profile not found"}), 404

    social = profile.social_links or {}
    for key in ["instagram", "twitter", "youtube", "spotify"]:
        if key in data:
            social[key] = data[key]

    result = update_profile(user_id, {"social_links": social})
    return jsonify(result)


@profile_bp.route('/api/me', methods=['DELETE'])
def api_delete_profile():
    """Delete user profile and all data."""
    user_id = get_user_id()
    result = delete_profile(user_id)
    if result["success"]:
        session.clear()
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
# ACTIVITY ROUTES
# ═══════════════════════════════════════════════════════════════

@profile_bp.route('/favorites')
def profile_favorites():
    """View all favorites."""
    user_id = ensure_profile()
    favorites = get_user_favorites(user_id, limit=100)
    return render_template('library.html', 
        songs=favorites, 
        title="My Favorites",
        section="favorites"
    )


@profile_bp.route('/history')
def profile_history():
    """View listening history."""
    user_id = ensure_profile()
    history = get_recently_played(user_id, limit=100)
    return render_template('library.html',
        songs=history,
        title="Listening History",
        section="history"
    )


@profile_bp.route('/playlists')
def profile_playlists():
    """View all playlists."""
    user_id = ensure_profile()
    playlists = get_user_playlists(user_id)
    return render_template('library.html',
        playlists=playlists,
        title="My Playlists",
        section="playlists"
    )
