"""
EvaMusic — Profile Routes
Cleaned up to completely remove broken taste tracker imports.
"""

from flask import Blueprint, render_template, request, jsonify, session
from models import (
    get_profile, update_profile, create_profile, 
    get_profile_stats, delete_profile,
    AVATAR_OPTIONS, THEME_OPTIONS, ACCENT_COLORS
)
from database import (
    get_user_favorites, get_recently_played, 
    get_user_playlists
)
import uuid

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
        session['username'] = f"user_{session['user_id']}"
    return session['user_id']

def ensure_profile():
    user_id = get_user_id()
    profile = get_profile(user_id)
    if not profile:
        username = session.get('username', f"user_{user_id}")
        create_profile(user_id, username)
    return user_id

@profile_bp.route('/')
def profile():
    user_id = ensure_profile()
    prof = get_profile(user_id)
    stats = get_profile_stats(user_id)
    
    # Empty fallbacks for deleted taste features
    taste = {
        'top_artists': [],
        'top_languages': [],
        'top_genres': [],
        'top_moods': [('Chill', 1)]
    }
    
    return render_template('profile.html',
        profile=prof,
        stats=stats,
        taste=taste,
        avatars=AVATAR_OPTIONS,
        themes=THEME_OPTIONS,
        accents=ACCENT_COLORS
    )

@profile_bp.route('/api/update', methods=['POST'])
def api_update_profile():
    user_id = get_user_id()
    data = request.get_json(silent=True) or {}
    result = update_profile(user_id, data)
    if result["success"] and "username" in data:
        session['username'] = data["username"]
    return jsonify(result)

@profile_bp.route('/api/social', methods=['POST'])
def api_update_social():
    user_id = get_user_id()
    data = request.get_json(silent=True) or {}
    social = {}
    for key in ["instagram", "twitter", "youtube", "spotify"]:
        if key in data:
            social[key] = data[key]
    result = update_profile(user_id, {"social_links": social})
    return jsonify(result)

@profile_bp.route('/api/me', methods=['DELETE'])
def api_delete_profile():
    user_id = get_user_id()
    result = delete_profile(user_id)
    if result["success"]:
        session.clear()
    return jsonify(result)

@profile_bp.route('/favorites')
def profile_favorites():
    user_id = ensure_profile()
    favorites = get_user_favorites(user_id)
    return render_template('library.html', 
        songs=favorites, 
        title=\"My Favorites\",
        section=\"favorites\"
    )

@profile_bp.route('/history')
def profile_history():
    user_id = ensure_profile()
    history = get_recently_played(user_id, limit=100)
    return render_template('library.html',
        songs=history,
        title=\"Listening History\",
        section=\"history\"
    )

@profile_bp.route('/playlists')
def profile_playlists():
    user_id = ensure_profile()
    playlists = get_user_playlists(user_id)
    return render_template('library.html',
        playlists=playlists,
        title=\"My Playlists\",
        section=\"playlists\"
)
                  
